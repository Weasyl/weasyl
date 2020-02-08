from __future__ import absolute_import

import os
from io import open

import arrow
import bcrypt
from publicsuffixlist import PublicSuffixList
from sqlalchemy.sql.expression import select

from libweasyl import security
from libweasyl import staff
from libweasyl.models.users import GuestSession

from weasyl import define as d
from weasyl import macro as m
from weasyl import emailer
from weasyl import moderation
from weasyl.error import WeasylError
from weasyl.sessions import create_session, create_guest_session


_EMAIL = 100
_PASSWORD = 10
_USERNAME = 25


def signin(request, userid, ip_address=None, user_agent=None):
    # Update the last login record for the user
    d.execute("UPDATE login SET last_login = %i WHERE userid = %i", [d.get_time(), userid])

    # Log the successful login and increment the login count
    d.append_to_log('login.success', userid=userid, ip=d.get_address())
    d.metric('increment', 'logins')

    # set the userid on the session
    sess = create_session(userid)
    sess.ip_address = ip_address
    sess.user_agent_id = get_user_agent_id(user_agent)
    sess.create = True

    if not isinstance(request.weasyl_session, GuestSession):
        request.pg_connection.delete(request.weasyl_session)
        request.pg_connection.flush()

    request.weasyl_session = sess


def get_user_agent_id(ua_string=None):
    """
    Retrieves and/or stores a user agent string, and returns the ID number for the DB record.
    :param ua_string: The user agent of a web browser or other web client
    :return: An integer representing the identifier for the record in the table corresponding to ua_string.
    """
    if not ua_string:
        return None
    else:
        # Store/Retrieve the UA
        return d.engine.scalar("""
            INSERT INTO user_agents (user_agent)
            VALUES (%(ua_string)s)
            ON CONFLICT (user_agent) DO
                UPDATE SET user_agent = %(ua_string)s
            RETURNING user_agent_id
        """, ua_string=ua_string[0:1024])


def signout(request):
    request.pg_connection.delete(request.weasyl_session)
    request.pg_connection.flush()
    request.weasyl_session = create_guest_session()

    # unset SFW-mode cookie on logout
    request.delete_cookie_on_response("sfwmode")


def authenticate_bcrypt(username, password, request, ip_address=None, user_agent=None):
    """
    Return a result tuple of the form (userid, error); `error` is None if the
    login was successful. Pass None as the `request` to authenticate a user
    without creating a new session.

    :param username: The username of the user attempting authentication.
    :param password: The user's claimed password to check against the stored hash.
    :param ip_address: The address requesting authentication.
    :param user_agent: The user agent string of the submitting client.

    Possible errors are:
    - "invalid"
    - "unexpected"
    - "banned"
    - "suspended"
    - "2fa" - Indicates the user has opted-in to 2FA. Additional authentication required.
    """
    # Check that the user entered potentially valid values for `username` and
    # `password` before attempting to authenticate them
    if not username or not password:
        return 0, "invalid"

    # Select the authentication data necessary to check that the the user-entered
    # credentials are valid
    query = d.engine.execute(
        "SELECT ab.userid, ab.hashsum, lo.settings, lo.twofa_secret FROM authbcrypt ab"
        " RIGHT JOIN login lo USING (userid)"
        " WHERE lo.login_name = %(name)s",
        name=d.get_sysname(username),
    ).first()

    if not query:
        return 0, "invalid"

    USERID, HASHSUM, SETTINGS, TWOFA = query
    HASHSUM = HASHSUM.encode('utf-8')

    d.metric('increment', 'attemptedlogins')

    unicode_success = bcrypt.checkpw(password.encode('utf-8'), HASHSUM)
    if not unicode_success and not bcrypt.checkpw(d.plaintext(password).encode('utf-8'), HASHSUM):
        # Log the failed login attempt in a security log if the account the user
        # attempted to log into is a privileged account
        if USERID in staff.MODS:
            d.append_to_log('login.fail', userid=USERID, ip=d.get_address())
            d.metric('increment', 'failedlogins')

        # Return a zero userid and an error code (indicating the entered password
        # was incorrect)
        return 0, "invalid"
    elif "b" in SETTINGS:
        # Return the proper userid and an error code (indicating the user's account
        # has been banned)
        return USERID, "banned"
    elif "s" in SETTINGS:
        suspension = moderation.get_suspension(USERID)

        if d.get_time() > suspension.release:
            d.execute("UPDATE login SET settings = REPLACE(settings, 's', '') WHERE userid = %i", [USERID])
            d.execute("DELETE FROM suspension WHERE userid = %i", [USERID])
            d._get_all_config.invalidate(USERID)
        else:
            # Return the proper userid and an error code (indicating the user's
            # account has been temporarily suspended)
            return USERID, "suspended"

    # Attempt to create a new session if this is a request to log in, then log the signin
    # if it succeeded.
    if request is not None:
        # If the user's record has ``login.twofa_secret`` set (not nulled), return that password authentication succeeded.
        if TWOFA:
            if not isinstance(request.weasyl_session, GuestSession):
                request.pg_connection.delete(request.weasyl_session)
                request.pg_connection.flush()
            request.weasyl_session = create_session(None)
            request.weasyl_session.additional_data = {}
            return USERID, "2fa"
        else:
            signin(request, USERID, ip_address=ip_address, user_agent=user_agent)

    status = None
    if not unicode_success:
        # Oops; the user's password was stored badly, but they did successfully authenticate.
        status = 'unicode-failure'
    # Either way, authentication succeeded, so return the userid and a status.
    return USERID, status


def passhash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(m.MACRO_BCRYPT_ROUNDS))


def password_secure(password):
    """
    Return True if the password meets requirements, else False.
    """
    return len(password) >= _PASSWORD


# form
#   username     email         month
#   password     emailcheck    year
#   passcheck    day

def create(form):
    # Normalize form data
    username = d.plaintext(form.username[:_USERNAME])
    sysname = d.get_sysname(username)

    email = emailer.normalize_address(form.email)
    emailcheck = emailer.normalize_address(form.emailcheck)

    password = form.password
    passcheck = form.passcheck
    if form.day and form.month and form.year:
        try:
            birthday = arrow.Arrow(int(form.year), int(form.month), int(form.day))
        except ValueError:
            raise WeasylError("birthdayInvalid")
    else:
        birthday = None

    # Check mismatched form data
    if password != passcheck:
        raise WeasylError("passwordMismatch")
    if email != emailcheck:
        raise WeasylError("emailMismatch")

    # Check invalid form data
    if birthday is None or d.age_in_years(birthday) < 13:
        raise WeasylError("birthdayInvalid")
    if not password_secure(password):
        raise WeasylError("passwordInsecure")
    if not email:
        raise WeasylError("emailInvalid")
    if is_email_blacklisted(email):
        raise WeasylError("emailBlacklisted")
    if not sysname or ";" in username:
        raise WeasylError("usernameInvalid")
    if sysname in ["admin", "administrator", "mod", "moderator", "weasyl",
                   "weasyladmin", "weasylmod", "staff", "security"]:
        raise WeasylError("usernameInvalid")
    if username_exists(sysname):
        raise WeasylError("usernameExists")

    # Account verification token
    token = security.generate_key(40)

    # Only attempt to create the account if the email is unused (as defined by the function)
    if not email_exists(email):
        # Create pending account
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
            "token": token,
            "username": username,
            "login_name": sysname,
            "hashpass": passhash(password),
            "email": email,
            "birthday": birthday,
            "unixtime": arrow.now(),
        })

        # Send verification email
        emailer.send(email, "Weasyl Account Creation", d.render(
            "email/verify_account.html", [token, sysname]))
        d.metric('increment', 'createdusers')
    else:
        # Store a dummy record to support plausible deniability of email addresses
        # So "reserve" the username, but mark the record invalid, and use the token to satisfy the uniqueness
        #  constraint for the email field (e.g., if there is already a valid, pending row in the table).
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
            "token": token,
            "username": username,
            "login_name": sysname,
            "hashpass": passhash(password),
            "email": token,
            "birthday": arrow.now(),
            "unixtime": arrow.now(),
            "invalid": True,
            # So we have a way for admins to determine which email address collided in the View Pending Accounts Page
            "invalid_email_addr": email,
        })
        # The email address in question is already in use in either `login` or `logincreate`;
        #   let the already registered user know this via email (perhaps they forgot their username/password)
        query_username_login = d.engine.scalar("SELECT login_name FROM login WHERE email = %(email)s", email=email)
        query_username_logincreate = d.engine.scalar("SELECT login_name FROM logincreate WHERE email = %(email)s", email=email)
        emailer.send(email, "Weasyl Account Creation - Account Already Exists", d.render(
            "email/email_in_use_account_creation.html", [query_username_login or query_username_logincreate]))


def verify(token, ip_address=None):
    lo = d.meta.tables["login"]
    lc = d.meta.tables["logincreate"]
    query = d.engine.execute(lc.select().where(lc.c.token == token)).first()

    # Did the token match a pending login create record?
    if not query:
        raise WeasylError("logincreateRecordMissing")
    elif query.invalid:
        # If the record is explicitly marked as invalid, treat the record as if it doesn't exist.
        raise WeasylError("logincreateRecordMissing")

    db = d.connect()
    with db.begin():
        # Create login record
        userid = db.scalar(lo.insert().returning(lo.c.userid), {
            "login_name": d.get_sysname(query.username),
            "last_login": arrow.now(),
            "email": query.email,
            "ip_address_at_signup": ip_address,
        })

        # Create profile records
        db.execute(d.meta.tables["authbcrypt"].insert(), {
            "userid": userid,
            "hashsum": query.hashpass,
        })
        db.execute(d.meta.tables["profile"].insert(), {
            "userid": userid,
            "username": query.username,
            "full_name": query.username,
            "unixtime": arrow.now(),
            "config": "kscftj",
        })
        db.execute(d.meta.tables["userinfo"].insert(), {
            "userid": userid,
            "birthday": query.birthday,
        })
        db.execute(d.meta.tables["userstats"].insert(), {
            "userid": userid,
        })
        db.execute(d.meta.tables["welcomecount"].insert(), {
            "userid": userid,
        })

        # Update logincreate records
        db.execute(lc.delete().where(lc.c.token == token))

    d.metric('increment', 'verifiedusers')


def email_exists(email):
    return d.engine.scalar("""
        SELECT
            EXISTS (SELECT 0 FROM login WHERE email = %(email)s) OR
            EXISTS (SELECT 0 FROM logincreate WHERE email = %(email)s)
    """, email=email)


def username_exists(login_name):
    return d.engine.scalar("""
        SELECT
            EXISTS (SELECT 0 FROM login WHERE login_name = %(name)s) OR
            EXISTS (SELECT 0 FROM useralias WHERE alias_name = %(name)s) OR
            EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)
    """, name=login_name)


def update_unicode_password(userid, password, password_confirm):
    if password != password_confirm:
        raise WeasylError('passwordMismatch')
    if not password_secure(password):
        raise WeasylError('passwordInsecure')

    hashpw = d.engine.scalar("""
        SELECT hashsum FROM authbcrypt WHERE userid = %(userid)s
    """, userid=userid).encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), hashpw):
        return

    if not bcrypt.checkpw(d.plaintext(password).encode('utf-8'), hashpw):
        raise WeasylError('passwordIncorrect')

    d.engine.execute("""
        UPDATE authbcrypt SET hashsum = %(hashsum)s WHERE userid = %(userid)s
    """, userid=userid, hashsum=passhash(password))


def get_account_verification_token(email=None, username=None):
    email = email and emailer.normalize_address(email)
    username = username and d.get_sysname(username)

    logincreate = d.meta.tables['logincreate']
    statement = select([logincreate.c.token])

    if email:
        statement = statement.where(logincreate.c.email.ilike(email))
    else:
        statement = statement.where(logincreate.c.login_name == username)

    return d.engine.scalar(statement)


with open(os.path.join(m.MACRO_SYS_CONFIG_PATH, "disposable-domains.txt"), encoding='ascii') as f:
    DISPOSABLE_DOMAINS = frozenset([line.rstrip() for line in f])


def is_email_blacklisted(address):
    """
    Determines if a supplied email address is present in the 'emailblacklist' table.
    Parameters:
        address: The email address to split out the domain from.
    Returns:
        Boolean True if present on the blacklist, or False otherwise.
    """
    _, domain = address.rsplit("@", 1)
    psl = PublicSuffixList()
    private_suffix = psl.privatesuffix(domain=domain)

    # Check the disposable email address list
    if private_suffix in DISPOSABLE_DOMAINS:
        return True

    # Check the explicitly defined/blacklisted domains.
    return d.engine.scalar(
        "SELECT EXISTS (SELECT FROM emailblacklist WHERE domain_name = %(domain)s)",
        domain=private_suffix,
    )


def verify_email_change(userid, token):
    """
    Verify a user's email change request, updating the `login` record if it validates.

    Compare a supplied token against the record within the `emailverify` table, and provided
    a match exists, copy the email within into the user's account record.

    Parameters:
        userid: The userid of the account to attempt to update.
        token: The security token to search for.

    Returns: The newly set email address when verification of the `token` was successful; raises
    a WeasylError upon unsuccessful verification.
    """
    # Sanity checks: Must have userid and token
    if not userid or not token:
        raise WeasylError("Unexpected")
    query_result = d.engine.scalar("""
        DELETE FROM emailverify
        WHERE userid = %(userid)s AND token = %(token)s
        RETURNING email
    """, userid=userid, token=token)
    if not query_result:
        raise WeasylError("ChangeEmailVerificationTokenIncorrect")
    else:
        d.engine.execute("""
            UPDATE login
            SET email = %(email)s
            WHERE userid = %(userid)s
        """, userid=userid, email=query_result)
        return query_result

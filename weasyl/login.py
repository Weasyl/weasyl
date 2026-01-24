import os
from dataclasses import dataclass
from typing import NamedTuple

import bcrypt
import sqlalchemy

from libweasyl import security
from libweasyl import staff

from weasyl import define as d
from weasyl import macro as m
from weasyl import emailer
from weasyl.error import WeasylError
from weasyl.sessions import create_session
from weasyl.forms import parse_sysname
from weasyl.users import Username
from weasyl.util.trie import Trie


_PASSWORD = 10


def signin(request, userid, ip_address=None, user_agent=None):
    if request.userid:
        raise WeasylError("Unexpected")  # pragma: no cover

    # Log the successful login and increment the login count
    d.append_to_log('login.success', userid=userid, ip=d.get_address())
    d.metric('increment', 'logins')

    with d.sessionmaker_future.begin() as tx:
        # Update the last login record for the user
        tx.execute("UPDATE login SET last_login = NOW() WHERE userid = :user", {"user": userid})

        sess = create_session(userid)
        sess.ip_address = ip_address
        sess.user_agent_id = get_user_agent_id(user_agent)
        tx.add(sess)

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
    with d.sessionmaker_future.begin() as tx:
        tx.delete(request.weasyl_session)

    request.weasyl_session = None


class Success(NamedTuple):
    userid: int


class SecondFactorRequired(NamedTuple):
    userid: int


@dataclass(frozen=True, slots=True)
class InvalidCredentials:
    username_exists: bool
    inactive_username_exists: bool


class Banned(NamedTuple):
    userid: int


class Suspended(NamedTuple):
    userid: int


def authenticate_bcrypt(
    username: str,
    password: str,
    request,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Success | SecondFactorRequired | InvalidCredentials | Banned | Suspended:
    """
    Authenticate a user using a set of credentials.

    :param username: The username of the user attempting authentication.
    :param password: The user's claimed password to check against the stored hash.
    :param request: The request on which to create a new session, or `None` to authenticate without creating a session.
    :param ip_address: The address requesting authentication.
    :param user_agent: The user agent string of the submitting client.
    """
    sysname = parse_sysname(username)
    del username

    # Check that the user entered potentially valid values for `username` and
    # `password` before attempting to authenticate them
    if sysname is None or not password:
        return InvalidCredentials(
            username_exists=False,
            inactive_username_exists=False,
        )

    # Select the authentication data necessary to check that the the user-entered
    # credentials are valid
    query = d.engine.execute(
        "SELECT ab.userid, ab.hashsum, lo.twofa_secret FROM authbcrypt ab"
        " RIGHT JOIN login lo USING (userid)"
        " WHERE lo.login_name = %(name)s",
        name=sysname,
    ).first()

    def former_username_exists(found_user: int | None) -> bool:
        # Check if an attempted username is the former username of some [other] user.
        # There’s no `NOT active` filter here: even an active former username can’t be used to log in.
        return d.engine.scalar(
            "SELECT EXISTS (SELECT FROM username_history WHERE login_name = %(name)s AND userid IS DISTINCT FROM %(found_user)s)",
            name=sysname,
            found_user=found_user,
        )

    if not query:
        return InvalidCredentials(
            username_exists=False,
            inactive_username_exists=former_username_exists(None),
        )

    USERID, HASHSUM, TWOFA = query
    HASHSUM = HASHSUM.encode('utf-8')
    IS_BANNED, IS_SUSPENDED = d.get_login_settings(USERID)

    d.metric('increment', 'attemptedlogins')

    if not bcrypt.checkpw(password.encode('utf-8'), HASHSUM):
        # Log the failed login attempt in a security log if the account the user
        # attempted to log into is a privileged account
        if USERID in staff.MODS:
            d.append_to_log('login.fail', userid=USERID, ip=d.get_address())
            d.metric('increment', 'failedlogins')

        return InvalidCredentials(
            username_exists=True,
            inactive_username_exists=former_username_exists(USERID),
        )
    elif IS_BANNED:
        # Return the proper userid and an error code (indicating the user's account
        # has been banned)
        return Banned(USERID)
    elif IS_SUSPENDED:
        from weasyl import moderation
        suspension = moderation.get_suspension(USERID)

        if d.get_time() > suspension.release:
            d.execute("DELETE FROM suspension WHERE userid = %i", [USERID])
            d._get_all_config.invalidate(USERID)
        else:
            # Return the proper userid and an error code (indicating the user's
            # account has been temporarily suspended)
            return Suspended(USERID)

    # Attempt to create a new session if this is a request to log in, then log the signin
    # if it succeeded.
    if request is not None:
        # If the user's record has ``login.twofa_secret`` set (not nulled), return that password authentication succeeded.
        if TWOFA:
            return SecondFactorRequired(USERID)
        else:
            signin(request, USERID, ip_address=ip_address, user_agent=user_agent)

    # Either way, authentication succeeded, so return the userid and a status.
    return Success(USERID)


def passhash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(m.MACRO_BCRYPT_ROUNDS)).decode('ascii')


def password_secure(password):
    """
    Return True if the password meets requirements, else False.
    """
    return len(password) >= _PASSWORD


def _delete_expired():
    """
    Delete expired logincreate records.
    """
    d.engine.execute("DELETE FROM logincreate WHERE created_at < now() - INTERVAL '2 days'")


def create(form):
    # Normalize form data
    username = Username.create(form.username)
    email = emailer.normalize_address(form.email)
    password = form.password

    # Check invalid form data
    if "age" not in form or form.age != "13+":
        raise WeasylError("birthdayInvalid")
    if not password_secure(password):
        raise WeasylError("passwordInsecure")
    if not email:
        raise WeasylError("emailInvalid")
    if _is_email_blacklisted(email):
        raise WeasylError("emailBlacklisted")

    # Delete stale logincreate records before checking for colliding ones or trying to insert more
    _delete_expired()

    if username_exists(username.sysname):
        raise WeasylError("usernameExists")

    # Account verification token
    token = security.generate_key(40)

    # Only attempt to create the account if the email is unused (as defined by the function)
    if not email_exists(email):
        # Create pending account
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
            "token": token,
            "username": username.display,
            "login_name": username.sysname,
            "hashpass": passhash(password),
            "email": email,
        })

        # Send verification email
        emailer.send(email, "Weasyl Account Creation", d.render(
            "email/verify_account.html", [token, username.sysname]))
        d.metric('increment', 'createdusers')
    else:
        # Store a dummy record to support plausible deniability of email addresses
        # So "reserve" the username, but mark the record invalid, and use the token to satisfy the uniqueness
        #  constraint for the email field (e.g., if there is already a valid, pending row in the table).
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
            "token": token,
            "username": username.display,
            "login_name": username.sysname,
            "hashpass": passhash(password),
            "email": token,
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


def initial_profile(userid: int, username: str):
    return {
        "userid": userid,
        "username": username,
        "full_name": username,
        "config": "kscftj",
        "commissions_status": "closed",
        "trades_status": "closed",
        "requests_status": "closed",
        "streaming_later": False,
        "show_age": False,
        "can_suggest_tags": True,
        "premium": False,
        "favorites_visibility": "everyone",
        "favorites_bar": True,
        "shouts_from": "everyone",
        "messages_from": "everyone",
        "profile_guests": True,
        "profile_stats": True,
        "max_rating": "general",
        "watch_defaults": "scftj",
        "thumbnail_bar": "submissions",
        "allow_collection_requests": True,
        "collection_notifs": True,
        "custom_thumbs": True,
    }


def verify(token, ip_address=None):
    # Delete stale logincreate records before verifying against them
    _delete_expired()

    lo = d.meta.tables["login"]
    lc = d.meta.tables["logincreate"]
    query = d.engine.execute(lc.select().where(lc.c.token == token)).first()

    # Did the token match a pending login create record?
    if not query:
        raise WeasylError("logincreateRecordMissing")
    elif query.invalid:
        # If the record is explicitly marked as invalid, treat the record as if it doesn't exist.
        raise WeasylError("logincreateRecordMissing")

    username = Username.from_stored(query.username)

    updateids = d.get_updateids()
    latest_updateid = updateids[0] if updateids else None

    db = d.connect()
    with db.begin():
        # Create login record
        userid = db.scalar(
            lo.insert().values(
                login_name=username.sysname,
                last_login=sqlalchemy.func.now(),
                email=query.email,
                ip_address_at_signup=ip_address,
                last_read_updateid=latest_updateid,
            ).returning(lo.c.userid))

        # Create profile records
        db.execute(d.meta.tables["authbcrypt"].insert(), {
            "userid": userid,
            "hashsum": query.hashpass,
        })
        db.execute(
            d.meta.tables["profile"].insert(),
            initial_profile(userid, username.display),
        )
        db.execute(d.meta.tables["userinfo"].insert(), {
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
            EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s) OR
            EXISTS (SELECT 0 FROM username_history WHERE active AND login_name = %(name)s)
    """, name=login_name)


def release_username(db, acting_user, target_user):
    old_sysname = db.scalar(
        "UPDATE username_history SET"
        " active = FALSE,"
        " deactivated_at = now(),"
        " deactivated_by = %(acting)s"
        " WHERE userid = %(target)s AND active"
        " RETURNING login_name",
        acting=acting_user,
        target=target_user,
    )

    d._get_userids.invalidate(old_sysname)


def change_username(acting_user, target_user, bypass_limit, new_username):
    new_username = Username.create(new_username)
    old_username = d.get_username(target_user)

    if new_username.display == old_username.display:
        return

    cosmetic = new_username.sysname == old_username.sysname

    def change_username_transaction(db):
        if not cosmetic and not bypass_limit:
            seconds = db.scalar(
                "SELECT extract(epoch from now() - replaced_at)::int8"
                " FROM username_history"
                " WHERE userid = %(target)s"
                " AND NOT cosmetic"
                " ORDER BY historyid DESC LIMIT 1",
                target=target_user,
            )

            if seconds is not None:
                days = seconds // (3600 * 24)

                if days < 30:
                    raise WeasylError("usernameChangedTooRecently")

        if not cosmetic:
            release_username(
                db,
                acting_user=acting_user,
                target_user=target_user,
            )

            conflict = db.scalar(
                "SELECT EXISTS (SELECT FROM login WHERE login_name = %(new_sysname)s AND userid != %(target)s)"
                " OR EXISTS (SELECT FROM useralias WHERE alias_name = %(new_sysname)s)"
                " OR EXISTS (SELECT FROM logincreate WHERE login_name = %(new_sysname)s)"
                " OR EXISTS (SELECT FROM username_history WHERE active AND login_name = %(new_sysname)s)",
                target=target_user,
                new_sysname=new_username.sysname,
            )

            if conflict:
                raise WeasylError("usernameExists")

        db.execute(
            "INSERT INTO username_history (userid, username, login_name, replaced_at, replaced_by, active, cosmetic)"
            " VALUES (%(target)s, %(old_username)s, %(old_sysname)s, now(), %(target)s, NOT %(cosmetic)s, %(cosmetic)s)",
            target=target_user,
            old_username=old_username.display,
            old_sysname=old_username.sysname,
            cosmetic=cosmetic,
        )

        if not cosmetic:
            result = db.execute(
                "UPDATE login SET login_name = %(new_sysname)s WHERE userid = %(target)s AND login_name = %(old_sysname)s",
                target=target_user,
                old_sysname=old_username.sysname,
                new_sysname=new_username.sysname,
            )

            if result.rowcount != 1:
                raise WeasylError("Unexpected")

        db.execute(
            "UPDATE profile SET username = %(new_username)s WHERE userid = %(target)s",
            target=target_user,
            new_username=new_username.display,
        )

    d.serializable_retry(change_username_transaction)
    d.username_invalidate(target_user)

    if not cosmetic:
        d._get_userids.invalidate(old_username.sysname)


with open(os.path.join(m.MACRO_SYS_CONFIG_PATH, "disposable-domains.txt"), encoding='ascii') as f:
    _DISPOSABLE_DOMAINS = Trie(reversed(line.rstrip().split(".")) for line in f)


# TODO: apply to e-mail changes
def _is_email_blacklisted(address: str) -> bool:
    _, domain = address.rsplit("@", 1)
    return _DISPOSABLE_DOMAINS.contains_prefix_of(reversed(domain.split(".")))


def authenticate_account_change(*, userid, password):
    """
    Check a password against an account, throwing WeasylError('passwordIncorrect') if it doesn’t match.

    Bans/suspensions and two-factor authentication aren’t checked.

    Returns the account’s e-mail address, because it’s convenient.
    """
    row = d.engine.execute(
        "SELECT email, hashsum FROM login INNER JOIN authbcrypt USING (userid) WHERE userid = %(user)s",
        {"user": userid},
    ).first()

    if not bcrypt.checkpw(password.encode('utf-8'), row.hashsum.encode('ascii')):
        raise WeasylError('passwordIncorrect')

    return row.email


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
    d.engine.execute("""
        DELETE FROM emailverify
        WHERE createtimestamp < (NOW() - INTERVAL '2 days')
    """)
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

# login.py

from __future__ import absolute_import

import arrow
import bcrypt
from sqlalchemy.sql.expression import select

from libweasyl import security
from libweasyl import staff

from weasyl import define as d
from weasyl import macro as m
from weasyl import emailer
from weasyl import moderation
from weasyl.error import WeasylError


_EMAIL = 100
_PASSWORD = 10
_USERNAME = 25


def signin(userid):
    # Update the last login record for the user
    d.execute("UPDATE login SET last_login = %i WHERE userid = %i", [d.get_time(), userid])

    # set the userid on the session
    sess = d.get_weasyl_session()
    sess.userid = userid
    sess.save = True


def signout(request):
    sess = request.weasyl_session
    # unset SFW-mode cookie on logout
    request.delete_cookie_on_response("sfwmode")
    if sess.additional_data.get('user-stack'):
        sess.userid = sess.additional_data['user-stack'].pop()
        sess.additional_data.changed()
    else:
        sess.userid = None
    sess.save = True


def authenticate_bcrypt(username, password, session=True):
    """
    Return a result tuple of the form (userid, error); `error` is None if the
    login was successful. Pass `session` as False to authenticate a user without
    creating a new session.

    Possible errors are:
    - "invalid"
    - "unexpected"
    - "address"
    - "banned"
    - "suspended"
    """
    # Check that the user entered potentially valid values for `username` and
    # `password` before attempting to authenticate them
    if not username or not password:
        return 0, "invalid"

    # Select the authentication data necessary to check that the the user-entered
    # credentials are valid
    query = d.execute("SELECT ab.userid, ab.hashsum, lo.settings FROM authbcrypt ab"
                      " RIGHT JOIN login lo USING (userid)"
                      " WHERE lo.login_name = '%s'", [d.get_sysname(username)], ["single"])

    if not query:
        return 0, "invalid"

    USERID, HASHSUM, SETTINGS = query
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
            d.get_login_settings.invalidate(USERID)
        else:
            # Return the proper userid and an error code (indicating the user's
            # account has been temporarily suspended)
            return USERID, "suspended"

    # Attempt to create a new session if `session` is True, then log the signin
    # if it succeeded.
    if session:
        signin(USERID)
        d.append_to_log('login.success', userid=USERID, ip=d.get_address())
        d.metric('increment', 'logins')

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
    if not sysname or ";" in username:
        raise WeasylError("usernameInvalid")
    if sysname in ["admin", "administrator", "mod", "moderator", "weasyl",
                   "weasyladmin", "weasylmod", "staff", "security"]:
        raise WeasylError("usernameInvalid")
    if email_exists(email):
        raise WeasylError("emailExists")
    if username_exists(sysname):
        raise WeasylError("usernameExists")

    # Create pending account
    token = security.generate_key(40)

    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": username,
        "login_name": sysname,
        "hashpass": passhash(password),
        "email": email,
        "birthday": birthday,
        "unixtime": arrow.now(),
    })

    # Queue verification email
    emailer.append([email], None, "Weasyl Account Creation", d.render(
        "email/verify_account.html", [token, sysname]))
    d.metric('increment', 'createdusers')


def verify(token):
    lo = d.meta.tables["login"]
    lc = d.meta.tables["logincreate"]
    query = d.engine.execute(lc.select().where(lc.c.token == token)).first()

    if not query:
        raise WeasylError("logincreateRecordMissing")

    db = d.connect()
    with db.begin():
        # Create login record
        userid = db.scalar(lo.insert().returning(lo.c.userid), {
            "login_name": d.get_sysname(query.username),
            "last_login": arrow.now(),
            "email": query.email,
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

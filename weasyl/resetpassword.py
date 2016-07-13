# resetpassword.py
# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError

from libweasyl import security
from weasyl import define as d
from weasyl import emailer
from weasyl.error import WeasylError


def checktoken(token):
    return d.execute("SELECT EXISTS (SELECT 0 FROM forgotpassword WHERE token = '%s')", [token], ["bool"])


# form
#   email       month
#   username    year
#   day

def request(form):
    token = security.generate_key(100)
    email = emailer.normalize_address(form.email)
    username = d.get_sysname(form.username)

    # Determine the user associated with `username`; if the user is not found,
    # raise an exception
    user = d.engine.execute(
        "SELECT userid, email FROM login WHERE login_name = %(username)s",
        username=username).first()

    if not user:
        raise WeasylError("loginRecordMissing")

    # Check the user's email address against the provided e-mail address,
    # raising an exception if there is a mismatch
    if email != emailer.normalize_address(user.email):
        raise WeasylError("emailInvalid")

    # Insert a record into the forgotpassword table for the user,
    # or update an existing one
    now = d.get_time()
    address = d.get_address()

    try:
        d.engine.execute(
            "INSERT INTO forgotpassword (userid, token, set_time, address)"
            " VALUES (%(id)s, %(token)s, %(time)s, %(address)s)",
            id=user.userid, token=token, time=now, address=address)
    except IntegrityError:
        # An IntegrityError will probably indicate that a password reset request
        # already exists and that the existing row should be updated. If the update
        # doesn't find anything, though, the original error should be re-raised.
        result = d.engine.execute("""
            UPDATE forgotpassword SET
                token = %(token)s,
                set_time = %(time)s,
                address = %(address)s
            WHERE userid = %(id)s
        """, id=user.userid, token=token, time=now, address=address)

        if result.rowcount != 1:
            raise

    # Generate and send an email to the user containing a password reset link
    emailer.append([email], None, "Weasyl Password Recovery", d.render("email/reset_password.html", [token]))


def prepare(token):
    # Remove records from the forgotpassword table which have been active for
    # more than one hour, regardless of whether or not the user has clicked the
    # associated link provided to them in the password reset request email, or
    # which have been visited but have not been removed by the password reset
    # script within five minutes of being visited
    d.execute("DELETE FROM forgotpassword WHERE set_time < %i OR link_time > 0 AND link_time < %i",
              [d.get_time() - 3600, d.get_time() - 300])

    # Set the unixtime record for which the link associated with `token` was
    # visited by the user
    d.execute("UPDATE forgotpassword SET link_time = %i WHERE token = '%s'",
              [d.get_time(), token])


# form
#   username    passcheck    month
#   email       token        year
#   password    day

def reset(form):
    import login

    # Raise an exception if `password` does not enter `passcheck` (indicating
    # that the user mistyped one of the fields) or if `password` does not meet
    # the system's password security requirements
    if form.password != form.passcheck:
        raise WeasylError("passwordMismatch")
    elif not login.password_secure(form.password):
        raise WeasylError("passwordInsecure")

    # Select the user information and record data from the forgotpassword table
    # pertaining to `token`, requiring that the link associated with the record
    # be visited no more than five minutes prior; if the forgotpassword record is
    # not found or does not meet this requirement, raise an exception
    query = d.execute("""
        SELECT lo.userid, lo.login_name, lo.email, fp.link_time, fp.address
        FROM login lo
            INNER JOIN userinfo ui USING (userid)
            INNER JOIN forgotpassword fp USING (userid)
        WHERE fp.token = '%s' AND fp.link_time > %i
    """, [form.token, d.get_time() - 300], options="single")

    if not query:
        raise WeasylError("forgotpasswordRecordMissing")

    USERID, USERNAME, EMAIL, LINKTIME, ADDRESS = query

    # Check `username` and `email` against known correct values and raise an
    # exception if there is a mismatch
    if emailer.normalize_address(form.email) != emailer.normalize_address(EMAIL):
        raise WeasylError("emailIncorrect")
    elif d.get_sysname(form.username) != USERNAME:
        raise WeasylError("usernameIncorrect")
    elif d.get_address() != ADDRESS:
        raise WeasylError("addressInvalid")

    # Update the authbcrypt table with a new password hash
    """ TODO TEMPORARY """
    try:
        d.execute("INSERT INTO authbcrypt VALUES (%i, '')", [USERID])
    except:
        pass

    d.execute("UPDATE authbcrypt SET hashsum = '%s' WHERE userid = %i", [login.passhash(form.password), USERID])

    d.execute("DELETE FROM forgotpassword WHERE token = '%s'", [form.token])


# form
#   password
#   passcheck

def force(userid, form):
    import login

    if form.password != form.passcheck:
        raise WeasylError("passwordMismatch")
    elif not login.password_secure(form.password):
        raise WeasylError("passwordInsecure")

    d.execute("UPDATE login SET settings = REPLACE(settings, 'p', '') WHERE userid = %i", [userid])
    d.execute("UPDATE authbcrypt SET hashsum = '%s' WHERE userid = %i", [login.passhash(form.password), userid])
    d.get_login_settings.invalidate(userid)

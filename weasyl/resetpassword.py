# encoding: utf-8

from __future__ import absolute_import

from libweasyl import security
from weasyl import define as d
from weasyl import emailer
from weasyl.error import WeasylError


# form
#   email

def request(form):
    token = security.generate_key(100)
    email = emailer.normalize_address(form.email)

    # Determine the user associated with `username`; if the user is not found,
    # raise an exception
    user_id = d.engine.scalar("""
        SELECT userid FROM login WHERE email = %(email)s
    """, email=email)

    # If `user_id` exists, then the supplied email was valid; if not valid, do nothing, raising
    #   no errors for plausible deniability of email existence
    if user_id:
        # Insert a record into the forgotpassword table for the user,
        # or update an existing one
        now = d.get_time()
        address = d.get_address()

        d.engine.execute("""
            INSERT INTO forgotpassword (userid, token, set_time, address)
            VALUES (%(id)s, %(token)s, %(time)s, %(address)s)
            ON CONFLICT (userid) DO UPDATE SET
                token = %(token)s,
                set_time = %(time)s,
                address = %(address)s
        """, id=user_id, token=token, time=now, address=address)

        # Generate and send an email to the user containing a password reset link
        emailer.send(email, "Weasyl Password Recovery", d.render("email/reset_password.html", [token]))


def prepare(token):
    # Remove records from the forgotpassword table which have been active for
    # more than one hour, regardless of whether or not the user has clicked the
    # associated link provided to them in the password reset request email, or
    # which have been visited but have not been removed by the password reset
    # script within five minutes of being visited
    d.engine.execute(
        "DELETE FROM forgotpassword WHERE set_time < %(set_cutoff)s OR link_time > 0 AND link_time < %(link_cutoff)s",
        set_cutoff=d.get_time() - 3600,
        link_cutoff=d.get_time() - 300,
    )

    # Set the unixtime record for which the link associated with `token` was
    # visited by the user
    result = d.engine.execute(
        "UPDATE forgotpassword SET link_time = %(now)s WHERE token = %(token)s",
        now=d.get_time(),
        token=token,
    )

    return result.rowcount == 1


# form
#   username    passcheck    month
#   email       token        year
#   password    day

def reset(form):
    from weasyl import login

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
    query = d.engine.execute("""
        SELECT lo.userid, lo.login_name, lo.email, fp.link_time, fp.address
        FROM login lo
            INNER JOIN userinfo ui USING (userid)
            INNER JOIN forgotpassword fp USING (userid)
        WHERE fp.token = %(token)s AND fp.link_time > %(cutoff)s
    """, token=form.token, cutoff=d.get_time() - 300).first()

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
    d.engine.execute(
        'INSERT INTO authbcrypt (userid, hashsum) VALUES (%(user)s, %(hash)s) '
        'ON CONFLICT (userid) DO UPDATE SET hashsum = %(hash)s',
        user=USERID, hash=login.passhash(form.password))

    d.engine.execute(
        "DELETE FROM forgotpassword WHERE token = %(token)s",
        token=form.token)


# form
#   password
#   passcheck

def force(userid, form):
    from weasyl import login

    if form.password != form.passcheck:
        raise WeasylError("passwordMismatch")
    elif not login.password_secure(form.password):
        raise WeasylError("passwordInsecure")

    d.engine.execute("UPDATE login SET settings = REPLACE(settings, 'p', '') WHERE userid = %(user)s", user=userid)
    d.engine.execute("UPDATE authbcrypt SET hashsum = %(new_hash)s WHERE userid = %(user)s", new_hash=login.passhash(form.password), user=userid)
    d._get_all_config.invalidate(userid)

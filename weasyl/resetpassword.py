# encoding: utf-8

from __future__ import absolute_import

import hashlib
import string
from collections import namedtuple

from libweasyl import security
from weasyl import define as d
from weasyl import emailer
from weasyl.error import WeasylError


Unregistered = namedtuple('Unregistered', ['email'])


def _hash_token(token):
    return hashlib.sha256(token.encode("ascii")).digest()


def request(email):
    token = security.generate_key(25, key_characters=string.digits + string.ascii_lowercase)
    token_sha256 = _hash_token(token)
    email = emailer.normalize_address(email)

    if email is None:
        raise WeasylError("emailInvalid")

    d.engine.execute(
        "INSERT INTO forgotpassword (email, token_sha256)"
        " VALUES (%(email)s, %(token_sha256)s)",
        email=email, token_sha256=bytearray(token_sha256))

    # Generate and send an email to the user containing a password reset link
    emailer.send(email, "Weasyl Account Recovery", d.render("email/reset_password.html", [token]))


def _find_reset_target(db, email):
    """
    Get information about the user whose password can be reset by access to the
    provided normalized e-mail address, or None if there is no such user.

    Matches the address case-insensitively, with priority given to a
    case-sensitive match if there are multiple matches.
    """
    matches = db.execute(
        "SELECT userid, email, username FROM login"
        " INNER JOIN profile USING (userid)"
        ' WHERE lower(email COLLATE "C") = %(email)s',
        email=email,
    ).fetchall()

    for match in matches:
        if match.email == email:
            return match

    # XXX: we sent an e-mail to the address in its entered form, but are
    # resetting the password of an account with a different case.
    #
    # that’s a vulnerability for a case-sensitive mail provider, but there’s
    # not much else we can do while remaining user-friendly, and being
    # case-sensitive as a mail provider is already exposing users to that kind
    # of risk all over.
    return matches[0] if matches else None


def prepare(token):
    token_sha256 = _hash_token(token)

    d.engine.execute(
        "DELETE FROM forgotpassword"
        " WHERE created_at < now() - INTERVAL '1 hour'"
    )

    email = d.engine.scalar(
        "SELECT email FROM forgotpassword WHERE token_sha256 = %(token_sha256)s",
        token_sha256=bytearray(token_sha256),
    )

    if email is None:
        # token expired, or never existed.
        return None

    reset_target = _find_reset_target(d.engine, email=email)

    if reset_target is None:
        # a password reset was requested for an e-mail address not belonging to an account.
        return Unregistered(email=email)

    return reset_target


def reset(token, password, passcheck, expect_userid, address):
    from weasyl import login

    token_sha256 = _hash_token(token)

    if password != passcheck:
        raise WeasylError("passwordMismatch")
    elif not login.password_secure(password):
        raise WeasylError("passwordInsecure")

    with d.engine.begin() as db:
        email = db.scalar(
            "DELETE FROM forgotpassword"
            " WHERE token_sha256 = %(token_sha256)s AND created_at >= now() - INTERVAL '1 hour'"
            " RETURNING email",
            token_sha256=bytearray(token_sha256),
        )

        if email is None:
            # token expired, or never existed.
            raise WeasylError("forgotpasswordRecordMissing")

        match = _find_reset_target(db, email=email)

        if match is None:
            # account changed e-mail addresses.
            raise WeasylError("forgotpasswordRecordMissing")

        if match.userid != expect_userid:
            # e-mail address changed accounts. possible, but very unusual.
            #
            # this is to make sure to never change the password of an account
            # different from the one promised on the form, not a security thing
            # – `expect_userid` is a hidden field of the form.
            raise WeasylError("forgotpasswordRecordMissing")

        # Update the authbcrypt table with a new password hash
        result = db.execute(
            "UPDATE authbcrypt SET hashsum = %(hash)s WHERE userid = %(user)s",
            user=match.userid,
            hash=login.passhash(password),
        )

        if result.rowcount != 1:
            raise WeasylError("Unexpected")

        db.execute(
            d.meta.tables["user_events"].insert({
                "userid": match.userid,
                "event": "password-reset",
                "data": {
                    "address": address,
                }
            })
        )


# form
#   password
#   passcheck

def force(userid, form):
    from weasyl import login

    if form.password != form.passcheck:
        raise WeasylError("passwordMismatch")
    elif not login.password_secure(form.password):
        raise WeasylError("passwordInsecure")

    d.engine.execute("UPDATE login SET force_password_reset = FALSE WHERE userid = %(user)s", user=userid)
    d.engine.execute("UPDATE authbcrypt SET hashsum = %(new_hash)s WHERE userid = %(user)s", new_hash=login.passhash(form.password), user=userid)
    d._get_all_config.invalidate(userid)

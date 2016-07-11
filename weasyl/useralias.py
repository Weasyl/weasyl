# useralias.py

from error import WeasylError
import define as d

import login


def select(userid, premium=True):
    if premium:
        return d.execute("SELECT alias_name FROM useralias WHERE userid = %i AND settings ~ 'p'", [userid], ["element"])
    else:
        return d.execute("SELECT alias_name FROM useralias WHERE userid = %i", [userid], ["element"])


def set(userid, username):
    if login.username_exists(username):
        raise WeasylError("usernameExists")
    elif not d.get_premium(userid):
        raise WeasylError("InsufficientPermissions")

    d.execute("DELETE FROM useralias WHERE userid = %i AND settings ~ 'p'", [userid])
    d.execute("INSERT INTO useralias VALUES (%i, '%s', 'p')", [userid, username])

from __future__ import absolute_import

from weasyl import define as d
from weasyl import login
from weasyl.error import WeasylError


def select(userid):
    return d.execute("SELECT alias_name FROM useralias WHERE userid = %i AND settings ~ 'p'", [userid], ["element"])


def set(userid, username):
    if login.username_exists(username):
        raise WeasylError("usernameExists")
    elif not d.get_premium(userid):
        raise WeasylError("InsufficientPermissions")

    d.execute("DELETE FROM useralias WHERE userid = %i AND settings ~ 'p'", [userid])
    d.execute("INSERT INTO useralias VALUES (%i, '%s', 'p')", [userid, username])

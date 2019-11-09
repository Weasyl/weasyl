from __future__ import absolute_import

from weasyl import define as d
from weasyl import login
from weasyl.error import WeasylError


def select(userid):
    return d.engine.scalar("SELECT alias_name FROM useralias WHERE userid = %(user)s AND settings ~ 'p'", user=userid)


def set(userid, username):
    if login.username_exists(username):
        raise WeasylError("usernameExists")
    elif not d.get_premium(userid):
        raise WeasylError("InsufficientPermissions")

    d.engine.execute("DELETE FROM useralias WHERE userid = %(user)s AND settings ~ 'p'", user=userid)
    d.engine.execute("INSERT INTO useralias VALUES (%(user)s, %(name)s, 'p')", user=userid, name=username)

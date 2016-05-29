# followuser.py

from error import WeasylError
import macro as m
import define as d

import welcome
import ignoreuser

from libweasyl import ratings

from weasyl.configuration_builder import create_configuration, BoolOption
from weasyl import media

from sqlalchemy.exc import IntegrityError

WatchSettings = create_configuration([
    BoolOption("submit", "s"),
    BoolOption("collect", "c"),
    BoolOption("char", "f"),
    BoolOption("stream", "t"),
    BoolOption("journal", "j"),
])


def check(userid, otherid, myself=False):
    if not userid or not otherid:
        return False
    if userid == otherid:
        return myself

    return d.execute("SELECT EXISTS (SELECT 0 FROM watchuser WHERE (userid, otherid) = (%i, %i))",
                     [userid, otherid], options="bool")


def list_followed(userid, settings=None, within=False, rating=ratings.GENERAL.code, friends=False):
    """
    Returns a list of users who are following the specified user.
    """
    statement = ["SELECT wu.userid FROM watchuser wu JOIN profile pr ON wu.userid = pr.userid WHERE wu.otherid = %i"]

    if settings:
        statement.append(" AND wu.settings ~ '%s'")

    if friends:
        statement.append("""
            AND (
                wu.userid IN (SELECT fu.userid FROM frienduser fu WHERE fu.otherid = wu.otherid AND fu.settings !~ 'p')
                OR wu.userid IN (SELECT fu.otherid FROM frienduser fu WHERE fu.userid = wu.otherid AND fu.settings !~ 'p'))
        """)

    if rating == ratings.EXPLICIT.code:
        # Only notify users who view explicit
        statement.append(" AND pr.config ~ 'p'")
    elif rating == ratings.MATURE.code:
        # Only notify users who view explicit or explicit
        statement.append(" AND pr.config ~ '[ap]'")
    elif rating == ratings.MODERATE.code:
        # Only notify users who view mature or explicit or explicit
        statement.append(" AND pr.config ~ '[map]'")

    return d.execute("".join(statement),
                     [userid, settings] if settings else [userid],
                     options=["within"] if within else [])


def select_settings(userid, otherid):
    query = d.execute("SELECT settings FROM watchuser WHERE (userid, otherid) = (%i, %i)", [userid, otherid], ["single"])

    if not query:
        raise WeasylError("watchuserRecordMissing")

    return query[0]


def select_followed(userid, otherid, limit=None, backid=None, nextid=None, choose=None, following=False):
    """
    Returns the users who are following the specified user; note that
    ``following`` need never be passed explicitly.
    """
    if following:
        statement = ["SELECT wu.otherid, pr.username, pr.config FROM watchuser wu"
                     " INNER JOIN profile pr ON wu.otherid = pr.userid"
                     " WHERE wu.userid = %i" % (otherid,)]
    else:
        statement = ["SELECT wu.userid, pr.username, pr.config FROM watchuser wu"
                     " INNER JOIN profile pr ON wu.userid = pr.userid"
                     " WHERE wu.otherid = %i" % (otherid,)]

    if userid:
        statement.append(m.MACRO_IGNOREUSER % (userid, "pr"))

    if backid:
        statement.append(" AND pr.username < (SELECT username FROM profile WHERE userid = %i)" % (backid,))
    elif nextid:
        statement.append(" AND pr.username > (SELECT username FROM profile WHERE userid = %i)" % (nextid,))

    if choose:
        statement.append(" ORDER BY RANDOM() LIMIT %i" % (choose,))
    else:
        statement.append(" ORDER BY pr.username%s LIMIT %i" % (" DESC" if backid else "", limit))

    query = [{
        "userid": i[0],
        "username": i[1],
    } for i in d.execute("".join(statement))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def select_following(userid, otherid, limit=None, backid=None, nextid=None, choose=None):
    """
    Returns the users whom the specified user is following.
    """
    return select_followed(userid, otherid, limit, backid, nextid, choose, following=True)


def manage_following(userid, limit, backid=None, nextid=None):
    state = [
        "SELECT pr.userid, pr.username, pr.config FROM watchuser wu"
        " JOIN profile pr ON wu.otherid = pr.userid"
        " WHERE wu.userid = %i" % (userid,)]

    if backid:
        state.append(" AND pr.username < (SELECT username FROM profile WHERE userid = %i)" % backid)
    elif nextid:
        state.append(" AND pr.username > (SELECT username FROM profile WHERE userid = %i)" % nextid)

    state.append(" ORDER BY pr.username")

    if backid:
        state.append(" DESC")

    state.append(" LIMIT %i" % limit)

    query = [{
        "userid": i[0],
        "username": i[1],
    } for i in d.execute("".join(state))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def insert(userid, otherid):
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    elif ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")

    try:
        d.execute("INSERT INTO watchuser VALUES (%i, %i, '%s')",
                  [userid, otherid, WatchSettings.from_code(d.get_config(userid)).to_code()])
    except IntegrityError:
        pass

    welcome.followuser_remove(userid, otherid)
    welcome.followuser_insert(userid, otherid)


def update(userid, otherid, watch_settings):
    d.execute("UPDATE watchuser SET settings = '%s' WHERE (userid, otherid) = (%i, %i)",
              [watch_settings.to_code(), userid, otherid])


def remove(userid, otherid):
    d.execute("DELETE FROM watchuser WHERE (userid, otherid) = (%i, %i)", [userid, otherid])

    welcome.followuser_remove(userid, otherid)

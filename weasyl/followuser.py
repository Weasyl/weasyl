from libweasyl import ratings

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl.configuration_builder import create_configuration, BoolOption
from weasyl.error import WeasylError

WatchSettings = create_configuration([
    BoolOption("submit", "s"),
    BoolOption("collect", "c"),
    BoolOption("char", "f"),
    BoolOption("stream", "t"),
    BoolOption("journal", "j"),
])


def list_followed(userid, settings, rating=ratings.GENERAL.code, friends=False) -> list[int]:
    """
    Returns a list of users who are following the specified user.
    """
    statement = [
        "SELECT wu.userid FROM watchuser wu JOIN profile pr ON wu.userid = pr.userid WHERE wu.otherid = %(user)s"
        " AND wu.settings ~ %(setting)s"
    ]

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
        # Only notify users who view mature or explicit
        statement.append(" AND pr.config ~ '[ap]'")

    return d.engine.execute(
        "".join(statement),
        user=userid,
        setting=settings,
    ).scalars().all()


def select_settings(userid, otherid):
    settings = d.engine.scalar(
        "SELECT settings FROM watchuser WHERE (userid, otherid) = (%(user)s, %(other)s)",
        user=userid,
        other=otherid,
    )

    if settings is None:
        raise WeasylError("watchuserRecordMissing")

    return settings


def select_followed(userid, otherid, limit=None, backid=None, nextid=None, following=False):
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

    statement.append(" ORDER BY pr.username%s LIMIT %i" % (" DESC" if backid else "", limit))

    query = [{
        "userid": i[0],
        "username": i[1],
    } for i in d.execute("".join(statement))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def select_following(userid, otherid, limit=None, backid=None, nextid=None):
    """
    Returns the users whom the specified user is following.
    """
    return select_followed(userid, otherid, limit, backid, nextid, following=True)


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

    d.engine.execute(
        'INSERT INTO watchuser (userid, otherid, settings) VALUES (%(user)s, %(other)s, %(settings)s) '
        'ON CONFLICT DO NOTHING',
        user=userid, other=otherid, settings=WatchSettings.from_code(d.get_config(userid)).to_code())

    from weasyl import welcome
    welcome.followuser_remove(userid, otherid)
    welcome.followuser_insert(userid, otherid)


def update(userid, otherid, watch_settings):
    d.engine.execute(
        "UPDATE watchuser SET settings = %(settings)s WHERE (userid, otherid) = (%(user)s, %(other)s)",
        settings=watch_settings.to_code(),
        user=userid,
        other=otherid,
    )


def remove(userid, otherid):
    d.execute("DELETE FROM watchuser WHERE (userid, otherid) = (%i, %i)", [userid, otherid])

    from weasyl import welcome
    welcome.followuser_remove(userid, otherid)

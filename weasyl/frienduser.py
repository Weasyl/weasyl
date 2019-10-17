

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


def check(userid, otherid, pending=False, myself=True):
    if not userid or not otherid:
        return False
    elif userid == otherid:
        return myself

    if pending:
        return d.execute(
            "SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%i, %i) OR (userid, otherid) = (%i, %i))",
            [userid, otherid, otherid, userid], options="bool")
    else:
        return d.execute(
            "SELECT EXISTS (SELECT 0 FROM frienduser WHERE ((userid, otherid) = (%i, %i) OR (userid, otherid) = (%i, %i))"
            " AND settings !~ 'p')", [userid, otherid, otherid, userid], options="bool")


def already_pending(userid, otherid, myself=True):
    if not userid or not otherid:
        return False
    if userid == otherid:
        return myself

    return d.execute(
        "SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%i, %i) AND settings ~ 'p')",
        [userid, otherid], options="bool")


def has_friends(otherid):
    return d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM frienduser WHERE %(user)s IN (userid, otherid) AND settings !~ 'p')",
        user=otherid,
    )


def select_friends(userid, otherid, limit=None, backid=None, nextid=None, choose=False):
    """
    Return accepted friends. If `choose` is an integer, results will be ordered
    randomly.
    """
    fr = d.meta.tables['frienduser']
    pr = d.meta.tables['profile']
    iu = d.meta.tables['ignoreuser']

    friends = d.sa.union(
        (d.sa
         .select([fr.c.otherid, pr.c.username, pr.c.config])
         .select_from(fr.join(pr, fr.c.otherid == pr.c.userid))
         .where(d.sa.and_(fr.c.userid == otherid, fr.c.settings.op('!~')('p')))),
        (d.sa
         .select([fr.c.userid, pr.c.username, pr.c.config])
         .select_from(fr.join(pr, fr.c.userid == pr.c.userid))
         .where(d.sa.and_(fr.c.otherid == otherid, fr.c.settings.op('!~')('p')))))
    friends = friends.alias('friends')

    query = d.sa.select(friends.c)

    if userid:
        query = query.where(
            ~friends.c.otherid.in_(d.sa.select([iu.c.otherid]).where(iu.c.userid == userid)))
    if backid:
        query = query.where(
            friends.c.username < d.sa.select([pr.c.username]).where(pr.c.userid == backid))
    elif nextid:
        query = query.where(
            friends.c.username > d.sa.select([pr.c.username]).where(pr.c.userid == nextid))

    if choose:
        query = query.order_by('RANDOM()')
    else:
        query = query.order_by(
            friends.c.username.desc() if backid else friends.c.username.asc())
        query = query.limit(limit)

    db = d.connect()
    query = [{
        "userid": r.otherid,
        "username": r.username,
    } for r in db.execute(query)]

    ret = (d.get_random_set(query, choose) if choose else query[::-1] if backid else query)
    media.populate_with_user_media(ret)
    return ret


def select_accepted(userid, limit=None, backid=None, nextid=None):
    result = []
    query = d.execute(
        "SELECT fr.userid, p1.username, p1.config, fr.otherid, p2.username, p2.config, fr.settings FROM frienduser fr"
        " INNER JOIN profile p1 ON fr.userid = p1.userid"
        " INNER JOIN profile p2 ON fr.otherid = p2.userid"
        " WHERE %i IN (fr.userid, fr.otherid) AND fr.settings !~ 'p'"
        " ORDER BY p1.username", [userid])

    for i in query:
        if i[0] != userid:
            result.append({
                "userid": i[0],
                "username": i[1],
                "settings": i[6],
            })
        else:
            result.append({
                "userid": i[3],
                "username": i[4],
                "settings": i[6],
            })

    media.populate_with_user_media(result)
    return result


def select_requests(userid, limit=None, backid=None, nextid=None):
    query = d.execute("SELECT fr.userid, pr.username, pr.config, fr.settings FROM frienduser fr"
                      " INNER JOIN profile pr ON fr.userid = pr.userid"
                      " WHERE fr.otherid = %i AND fr.settings ~ 'p'", [userid])

    ret = [{
        "userid": i[0],
        "username": i[1],
        "settings": i[3],
    } for i in query]

    media.populate_with_user_media(ret)
    return ret


def request(userid, otherid):
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    elif ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")

    if d.execute("SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%i, %i) AND settings ~ 'p')",
                 [otherid, userid], options="bool"):
        d.execute("UPDATE frienduser SET settings = REPLACE(settings, 'p', '') WHERE (userid, otherid) = (%i, %i)",
                  [otherid, userid])

        welcome.frienduseraccept_insert(userid, otherid)
        welcome.frienduserrequest_remove(userid, otherid)
    elif not d.execute("SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%i, %i) AND settings ~ 'p')",
                       [userid, otherid], options="bool"):
        d.execute("INSERT INTO frienduser VALUES (%i, %i)", [userid, otherid])

        welcome.frienduserrequest_remove(userid, otherid)
        welcome.frienduserrequest_insert(userid, otherid)


def accept(userid, otherid):
    if check(userid, otherid):
        raise WeasylError("Unexpected")

    d.execute("UPDATE frienduser SET settings = REPLACE(settings, 'p', '')"
              " WHERE (userid, otherid) = (%i, %i)", [otherid, userid])
    welcome.frienduseraccept_insert(userid, otherid)
    welcome.frienduserrequest_remove(userid, otherid)


def remove(userid, otherid):
    d.execute("DELETE FROM frienduser WHERE userid IN (%i, %i) AND otherid IN (%i, %i)",
              [userid, otherid, userid, otherid])
    welcome.frienduseraccept_remove(userid, otherid)
    welcome.frienduserrequest_remove(userid, otherid)


def remove_request(userid, otherid):
    d.execute(
        "DELETE FROM frienduser "
        "WHERE userid IN (%i, %i) "
        "AND otherid IN (%i, %i)",
        [userid, otherid, userid, otherid])
    welcome.frienduserrequest_remove(userid, otherid)

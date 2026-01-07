import sqlalchemy as sa

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


def check(userid, otherid):
    """
    Check whether two users are confirmed friends.

    A user is considered their own friend.
    """
    if not userid or not otherid:
        return False

    if userid == otherid:
        return True

    return d.engine.scalar(
        "SELECT EXISTS (SELECT FROM frienduser"
        " WHERE ((userid, otherid) = (%(user)s, %(other)s) OR (userid, otherid) = (%(other)s, %(user)s))"
        " AND settings !~ 'p')",
        user=userid,
        other=otherid,
    )


def has_friends(otherid):
    return d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM frienduser WHERE %(user)s IN (userid, otherid) AND settings !~ 'p')",
        user=otherid,
    )


def select_friends(userid, otherid, limit=None, backid=None, nextid=None):
    """
    Return accepted friends.
    """
    fr = d.meta.tables['frienduser']
    pr = d.meta.tables['profile']
    iu = d.meta.tables['ignoreuser']

    friends = sa.union(
        (sa
         .select([fr.c.otherid, pr.c.username, pr.c.config])
         .select_from(fr.join(pr, fr.c.otherid == pr.c.userid))
         .where(sa.and_(fr.c.userid == otherid, fr.c.settings.op('!~')('p')))),
        (sa
         .select([fr.c.userid, pr.c.username, pr.c.config])
         .select_from(fr.join(pr, fr.c.userid == pr.c.userid))
         .where(sa.and_(fr.c.otherid == otherid, fr.c.settings.op('!~')('p')))))
    friends = friends.alias('friends')

    query = sa.select(friends.c)

    if userid:
        query = query.where(
            ~friends.c.otherid.in_(sa.select([iu.c.otherid]).where(iu.c.userid == userid)))
    if backid:
        query = query.where(
            friends.c.username < sa.select([pr.c.username]).where(pr.c.userid == backid).scalar_subquery())
    elif nextid:
        query = query.where(
            friends.c.username > sa.select([pr.c.username]).where(pr.c.userid == nextid).scalar_subquery())

    query = query.order_by(
        friends.c.username.desc() if backid else friends.c.username.asc())
    query = query.limit(limit)

    db = d.connect()
    query = [{
        "userid": r.otherid,
        "username": r.username,
    } for r in db.execute(query)]

    ret = query[::-1] if backid else query
    media.populate_with_user_media(ret)
    return ret


def select_accepted(userid):
    result = []
    query = d.execute(
        "SELECT fr.userid, p1.username, fr.otherid, p2.username FROM frienduser fr"
        " INNER JOIN profile p1 ON fr.userid = p1.userid"
        " INNER JOIN profile p2 ON fr.otherid = p2.userid"
        " WHERE %i IN (fr.userid, fr.otherid) AND fr.settings !~ 'p'"
        " ORDER BY p1.username", [userid])

    for i in query:
        if i[0] != userid:
            result.append({
                "userid": i[0],
                "username": i[1],
            })
        else:
            result.append({
                "userid": i[2],
                "username": i[3],
            })

    media.populate_with_user_media(result)
    return result


def select_requests(userid):
    query = d.execute("SELECT fr.userid, pr.username, fr.settings FROM frienduser fr"
                      " INNER JOIN profile pr ON fr.userid = pr.userid"
                      " WHERE fr.otherid = %i AND fr.settings ~ 'p'", [userid])

    ret = [{
        "userid": i[0],
        "username": i[1],
        "settings": i[2],
    } for i in query]

    media.populate_with_user_media(ret)
    return ret


def request(userid: int, otherid: int) -> None:
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    elif ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")

    with d.engine.begin() as tx:
        settings = tx.scalar(
            "INSERT INTO frienduser AS fu (userid, otherid)"
            " VALUES (%(userid)s, %(otherid)s)"
            " ON CONFLICT (least(userid, otherid), (userid # otherid))"
            " DO UPDATE SET settings = ''"
            " WHERE (fu.userid, fu.otherid) = (%(otherid)s, %(userid)s)"
            " AND fu.settings = 'p'"
            " RETURNING settings",
            userid=userid,
            otherid=otherid,
        )

        match settings:
            case None:
                # conflict, and `WHERE` clause didn't match: friendship already exists or friend request from this direction already exists
                pass

            case "":
                # conflict, and `WHERE` clause did match: pending friendship in the other direction existed, and is now accepted
                welcome.frienduserrequest_remove_exact(tx, otherid, userid)
                welcome.frienduseraccept_insert(tx, userid, otherid)

            case _:
                assert settings == "p"
                # no conflict: friend request from this direction was created
                welcome.frienduserrequest_remove_exact(tx, userid, otherid)
                welcome.frienduserrequest_insert(tx, userid, otherid)


def remove(userid, otherid):
    d.execute("DELETE FROM frienduser WHERE userid IN (%i, %i) AND otherid IN (%i, %i)",
              [userid, otherid, userid, otherid])
    welcome.frienduseraccept_remove(userid, otherid)
    welcome.frienduserrequest_remove(userid, otherid)


def remove_request(sender: int, recipient: int) -> None:
    """
    Remove a pending friend request sent by `sender` to `recipient`.

    Does nothing if the friend request is already accepted, was sent in the other direction, or doesn't exist.
    """
    with d.engine.begin() as tx:
        tx.execute(
            "DELETE FROM frienduser"
            " WHERE (userid, otherid) = (%(sender)s, %(recipient)s)"
            " AND settings ~ 'p'",
            sender=sender,
            recipient=recipient,
        )
        welcome.frienduserrequest_remove_exact(tx, sender, recipient)

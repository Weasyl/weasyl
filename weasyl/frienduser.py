import sqlalchemy as sa

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


def check(userid: int, otherid: int) -> bool:
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


def has_friends(otherid: int) -> bool:
    return d.engine.scalar(
        "SELECT EXISTS (SELECT FROM frienduser WHERE %(user)s IN (userid, otherid) AND settings !~ 'p')",
        user=otherid,
    )


def select_friends(
    userid: int,
    otherid: int,
    limit: int | None = None,
    backid: int = 0,
    nextid: int = 0,
):
    """
    Return accepted friends.
    """
    fr = d.meta.tables['frienduser']
    pr = d.meta.tables['profile']
    iu = d.meta.tables['ignoreuser']

    friends = sa.union(
        (sa
         .select([fr.c.otherid, pr.c.username])
         .select_from(fr.join(pr, fr.c.otherid == pr.c.userid))
         .where(sa.and_(fr.c.userid == otherid, fr.c.settings.op('!~')('p')))),
        (sa
         .select([fr.c.userid, pr.c.username])
         .select_from(fr.join(pr, fr.c.userid == pr.c.userid))
         .where(sa.and_(fr.c.otherid == otherid, fr.c.settings.op('!~')('p')))))
    friends = friends.alias('friends')

    query = sa.select(friends.c)

    if userid and userid != otherid:
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

    if limit is not None:
        query = query.limit(limit)

    db = d.connect()
    query = [{
        "userid": r.otherid,
        "username": r.username,
    } for r in db.execute(query)]

    ret = query[::-1] if backid else query
    media.populate_with_user_media(ret)
    return ret


def select_requests(userid: int):
    query = d.engine.execute(
        "SELECT fr.userid, pr.username FROM frienduser fr"
        " INNER JOIN profile pr ON fr.userid = pr.userid"
        " WHERE fr.otherid = %(user)s AND fr.settings ~ 'p'",
        user=userid,
    )

    ret = [row._asdict() for row in query]
    media.populate_with_user_media(ret)
    return ret


def request(userid: int, otherid: int) -> None:
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    elif ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")

    def transaction(tx) -> None:
        settings = tx.scalar(
            "INSERT INTO frienduser AS fu (userid, otherid)"
            " VALUES (%(userid)s, %(otherid)s)"
            " ON CONFLICT (least(userid, otherid), (userid # otherid))"
            " DO UPDATE SET settings = '', accepted_at = now()"
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
                welcome.frienduserrequest_remove(tx, sender=otherid, recipient=userid)
                welcome.frienduseraccept_insert(tx, requester=otherid, acceptor=userid)

            case _:
                assert settings == "p"
                # no conflict: friend request from this direction was created
                welcome.frienduserrequest_remove(tx, sender=userid, recipient=otherid)
                welcome.frienduserrequest_insert(tx, sender=userid, recipient=otherid)

    d.serializable_retry(transaction)


def remove(userid: int, otherid: int) -> None:
    def transaction(tx) -> None:
        row = tx.execute(
            "DELETE FROM frienduser"
            " WHERE (userid, otherid) = (%(user)s, %(other)s)"
            " OR (userid, otherid) = (%(other)s, %(user)s)"
            " RETURNING userid, otherid, settings ~ 'p' AS pending",
            user=userid,
            other=otherid,
        ).one_or_none()

        if row is None:
            # No friendship or friend request to remove.
            return

        if row.pending:
            welcome.frienduserrequest_remove(tx, sender=row.userid, recipient=row.otherid)
        else:
            welcome.frienduseraccept_remove(tx, requester=row.userid, acceptor=row.otherid)

    d.serializable_retry(transaction)


def remove_request(sender: int, recipient: int) -> None:
    """
    Remove a pending friend request sent by `sender` to `recipient`.

    Does nothing if the friend request is already accepted, was sent in the other direction, or doesn't exist.
    """
    def transaction(tx) -> None:
        tx.execute(
            "DELETE FROM frienduser"
            " WHERE (userid, otherid) = (%(sender)s, %(recipient)s)"
            " AND settings ~ 'p'",
            sender=sender,
            recipient=recipient,
        )
        welcome.frienduserrequest_remove(tx, sender=sender, recipient=recipient)

    d.serializable_retry(transaction)

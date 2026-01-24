import sqlalchemy as sa

from libweasyl.models import content, site, users
from libweasyl import ratings

from . import define as d, folder, followuser
from weasyl.error import WeasylError

"""
In this module, `userid` is typically the user performing the action, whereas
`otherid` is the user being acted upon, where present.
"""


def _insert(sender, referid, targetid, type, notify_users: list[int]) -> None:
    """
    Creates message notifications.
    """
    if not notify_users:
        return

    d.engine.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type)"
        " SELECT notify, %(sender)s, %(referid)s, %(targetid)s, %(now)s, %(type)s"
        " FROM UNNEST (%(notify)s) AS notify",
        sender=sender,
        referid=referid,
        targetid=targetid,
        now=d.get_time(),
        type=type,
        notify=notify_users,
    )


# notifications
#   2010 user posted submission

def submission_insert(userid, submitid, rating=ratings.GENERAL.code, friends_only=False):
    if folder.submission_has_folder_flag(submitid, 'n'):
        return

    statement = ["SELECT wu.userid FROM watchuser wu"
                 " INNER JOIN profile pr USING (userid)"
                 " WHERE wu.otherid = %(sender)s AND wu.settings ~ 's'"]

    if friends_only:
        statement.append(
            " AND (wu.userid IN (SELECT fu.userid FROM frienduser fu WHERE "
            "fu.otherid = wu.otherid AND fu.settings !~ 'p') "
            "OR wu.userid IN (SELECT fu.otherid FROM frienduser fu WHERE "
            "fu.userid = wu.otherid AND fu.settings !~ 'p'))")

    if rating == ratings.EXPLICIT.code:
        statement.append(" AND pr.config ~ 'p'")
    elif rating == ratings.MATURE.code:
        statement.append(" AND pr.config ~ '[ap]'")

    statement.append(
        " AND NOT EXISTS (SELECT 0 FROM searchmapsubmit WHERE "
        "targetid = %(sub)s AND tagid IN (SELECT tagid FROM blocktag WHERE userid = "
        "wu.userid AND rating <= %(rating)s))")

    _insert(userid, 0, submitid, 2010, d.engine.execute("".join(statement), sender=userid, sub=submitid, rating=rating).scalars().all())


# notifications
#   2010 user posted submission
#   2030 user collected submission
#   3020 user favorited submission
#   3030 offered collection to user
#   3050 user favourited collected submission
#   4020 user posted submission comment
#   4025 user replied to submission comment
#   4050 comment on item collected by other user

def _queries_for_submission_notifications(submitid):
    """
    Returns a list of SQLAlchemy conditions suitable to use to delete all
    notifications related to a submission
    """
    db = d.connect()
    return [
        ((site.SavedNotification.targetid == submitid) &
         (site.SavedNotification.type.in_([2010, 2030]))),
        ((site.SavedNotification.otherid == submitid) &
         (site.SavedNotification.type == 3140)),
        sa.or_(sa.and_(site.SavedNotification.targetid == submitid,
                       site.SavedNotification.type == 3030),
               sa.and_(site.SavedNotification.referid == submitid,
                       site.SavedNotification.type.in_([3020, 3050, 4050]))),
        ((site.SavedNotification.targetid.in_(db.query(content.Comment.commentid)
                                              .filter(content.Comment.target_sub == submitid))) &
         site.SavedNotification.type.in_([4020, 4025]))
    ]


def submission_remove(submitid):
    db = d.connect()
    deletes = _queries_for_submission_notifications(submitid)
    db.query(site.SavedNotification).filter(sa.or_(*deletes)).delete(synchronize_session=False)


def submission_became_friends_only(submitid, ownerid):
    """
    Called whenever a submission becomes friends only, to remove it from
    notification lists for users who are not currently friends with the
    owner.
    """
    db = d.connect()
    deletes = _queries_for_submission_notifications(submitid)
    non_friends_check = sa.and_(
        (~site.SavedNotification.userid.in_((db.query(users.Friendship.userid)
                                             .filter((users.Friendship.otherid == ownerid) &
                                                     (~users.Friendship.settings.op('~')('p')))))),
        (~site.SavedNotification.userid.in_((db.query(users.Friendship.otherid)
                                             .filter((users.Friendship.userid == ownerid) &
                                                     (~users.Friendship.settings.op('~')('p')))))))

    (db.query(site.SavedNotification).filter(non_friends_check)
       .filter(sa.or_(*deletes)).delete(synchronize_session=False))


# notifications
#   2050 user posted character

def character_insert(userid, charid, rating=ratings.GENERAL.code, *, friends_only):
    _insert(userid, 0, charid, 2050,
            followuser.list_followed(userid, "f", rating=rating, friends=friends_only))


# notifications
#   2050 user submitted character
#   3100 user favorited character
#   4040 user posted character comment
#   4045 user replied to character comment

def character_remove(charid):
    d.execute("DELETE FROM welcome WHERE (targetid, type) = (%i, 2050)", [charid])
    d.execute("DELETE FROM welcome WHERE (referid, type) = (%i, 3100)", [charid])
    d.execute("DELETE FROM welcome WHERE targetid IN (SELECT commentid FROM charcomment WHERE targetid = %i)"
              " AND type IN (4040, 4045)", [charid])


# notifications
#   2030 user collected submission

def collection_insert(userid, submitid):
    if folder.submission_has_folder_flag(submitid, 'n'):
        return

    query = """
        INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type)
        SELECT watchuser.userid, %(sender)s, 0, %(submission)s, %(now)s, %(type)s
        FROM watchuser
            INNER JOIN profile USING (userid)
        WHERE watchuser.otherid = %(sender)s
            AND watchuser.settings ~ 'c'
            AND profile.config ~ (
                CASE (SELECT rating FROM submission WHERE submitid = %(submission)s)
                    WHEN {explicit} THEN 'p'
                    WHEN {mature} THEN '[ap]'
                    ELSE ''
                END
            )
            AND NOT EXISTS (
                SELECT 0 FROM searchmapsubmit
                WHERE searchmapsubmit.targetid = %(submission)s
                    AND searchmapsubmit.tagid IN (
                        SELECT blocktag.tagid FROM blocktag
                        WHERE blocktag.userid = watchuser.userid
                            AND blocktag.rating <= (SELECT rating FROM submission WHERE submitid = %(submission)s)
                    )
            )
    """.format(
        explicit=ratings.EXPLICIT.code,
        mature=ratings.MATURE.code,
    )

    d.engine.execute(
        query,
        sender=userid,
        submission=submitid,
        now=d.get_time(),
        type=2030)


def collection_remove(userid, remove):
    d.engine.execute("""
        DELETE FROM welcome
        WHERE otherid = %(user)s
            AND type = 2030
            AND targetid = ANY (%(remove)s)
    """, user=userid, remove=remove)


# notifications
#   1010 user posted journal

def journal_insert(userid, journalid, *, rating, friends_only):
    _insert(
        userid, 0, journalid, 1010,
        followuser.list_followed(userid, "j", rating=rating, friends=friends_only))


# notifications
#   1010 user posted journal
#   3110 user favorited journal
#   4030 user posted journal comment
#   4035 user replied to journal comment

def journal_remove(journalid):
    d.engine.execute(
        "DELETE FROM welcome WHERE targetid = %(journal)s AND type = 1010"
        " OR referid = %(journal)s AND type = 3110"
        " OR targetid IN (SELECT commentid FROM journalcomment WHERE targetid = %(journal)s) AND type IN (4030, 4035)",
        journal=journalid)


# notifications
#   3030 collection offer to user

def collectoffer_insert(userid, otherid, submitid):
    d.engine.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) "
        "VALUES (%(user)s, %(other)s, 0, %(target)s, %(now)s, 3030)",
        user=otherid, other=userid, target=submitid, now=d.get_time())


# notifications
#   3035 collection requested by user

def collectrequest_insert(userid, otherid, submitid):
    d.engine.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) "
        "VALUES (%(user)s, %(other)s, 0, %(target)s, %(now)s, 3035)",
        user=otherid, other=userid, target=submitid, now=d.get_time())


# notifications
#   3030 collection offer to user
#   3035 collection request by user

def collectrequest_remove(userid, otherid, submitid):
    if otherid == userid:
        d.engine.execute("DELETE FROM welcome WHERE (userid, type, targetid) = (%(user)s, 3030, %(submit)s)",
                         user=userid, submit=submitid)
    else:
        d.engine.execute("DELETE FROM welcome "
                         "WHERE (userid, otherid, type, targetid) = (%(user)s, %(other)s, 3035, %(submit)s)",
                         user=userid, other=otherid, submit=submitid)


# notifications
#   3020 user favorited submission
#   3050 user favorited collected submission
#   3100 user favorited character
#   3110 user favorited journal

def favorite_insert(db, userid, *, submitid: int | None, charid, journalid, otherid):
    if submitid:
        ownerid = d.get_ownerid(submitid=submitid)
        notiftype = 3020 if ownerid == otherid else 3050
    elif charid:
        notiftype = 3100
    elif journalid:
        notiftype = 3110
    else:
        raise WeasylError("Unexpected")

    db.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%s, %s, %s, 0, %s, %s)",
        (otherid, userid, d.get_targetid(submitid, charid, journalid), d.get_time(), notiftype),
    )


# notifications
#   3020 user favorited submission
#   3100 user favorited character
#   3110 user favorited journal

def favorite_remove(db, userid, submitid=None, charid=None, journalid=None):
    db.execute(
        "DELETE FROM welcome WHERE (otherid, referid, type) = (%(user)s, %(refer)s, %(type)s)",
        user=userid,
        refer=d.get_targetid(submitid, charid, journalid),
        type=3020 if submitid else 3100 if charid else 3110,
    )


# notifications
#   4010 shout comment

def shout_insert(userid, commentid, otherid):
    d.execute("INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type)"
              " VALUES (%i, %i, 0, %i, %i, 4010)", [otherid, userid, commentid, d.get_time()])


# notifications
#   4015 shout comment reply
#   4016 staff note reply

def shoutreply_insert(userid, commentid, otherid, parentid, staffnote=False):
    d.execute("INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) "
              "VALUES (%i, %i, %i, %i, %i, %i)",
              [otherid, userid, parentid, commentid, d.get_time(), 4016 if staffnote else 4015])


# notifications
#   4020 submission comment
#   4030 journal comment
#   4040 character comment
#   4050 collection comment
#   4060 site update comment

def comment_insert(userid, commentid, otherid, submitid: int, charid, journalid, updateid):
    assert otherid

    if submitid:
        ownerid = d.get_ownerid(submitid=submitid)
        notiftype = 4020 if ownerid == otherid else 4050
    elif charid:
        notiftype = 4040
    elif journalid:
        notiftype = 4030
    elif updateid:
        notiftype = 4060
    else:
        raise WeasylError("Unexpected")

    d.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%i, %i, %i, %i, %i, %i)",
        [otherid, userid, d.get_targetid(submitid, charid, journalid, updateid), commentid, d.get_time(), notiftype])


# notifications
#   4010 shout comment
#   4015 shout comment reply
#   4020 submission comment
#   4025 submission comment reply
#   4030 journal comment
#   4035 journal comment reply
#   4040 character comment
#   4045 character comment reply
#   4060 site update comment
#   4065 site update comment reply

def comment_remove(commentid, feature):
    comment_code = {
        'shout': 4010,
        'submit': 4020,
        'char': 4040,
        'journal': 4030,
        'siteupdate': 4060,
    }[feature]
    reply_code = comment_code + 5

    if feature == 'submit' or feature == 'shout':
        recursive_ids = d.engine.execute("""WITH RECURSIVE rc AS (
              SELECT commentid FROM comments WHERE commentid = %s
              UNION ALL
              SELECT comments.commentid FROM comments
              INNER JOIN rc ON parentid = rc.commentid
            ) SELECT commentid FROM rc""", commentid)
    else:
        recursive_ids = d.engine.execute("""WITH RECURSIVE rc AS (
              SELECT commentid FROM %(feature)scomment WHERE commentid = %%(comment)s
              UNION ALL
              SELECT %(feature)scomment.commentid FROM %(feature)scomment
              INNER JOIN rc ON parentid = rc.commentid
            ) SELECT commentid FROM rc""" % {'feature': feature}, comment=commentid)

    recursive_ids = [x['commentid'] for x in recursive_ids]

    # `targetid` is the notification comment id, and `referid` is the post id for a top-level comment or the parent comment id for a reply
    result = d.engine.execute(
        """
        DELETE FROM welcome WHERE type IN (%(comment_code)s, %(reply_code)s) AND
        targetid = ANY (%(ids)s)
        RETURNING userid
        """, comment_code=comment_code, reply_code=reply_code, ids=recursive_ids)
    d.page_header_info_invalidate_multi({row.userid for row in result})


# notifications
#   4025 submission comment reply
#   4035 journal comment reply
#   4045 character comment reply
#   4065 site update comment reply

def commentreply_insert(userid, commentid, otherid, parentid, submitid, charid, journalid, updateid):
    if submitid:
        notiftype = 4025
    elif charid:
        notiftype = 4045
    elif journalid:
        notiftype = 4035
    elif updateid:
        notiftype = 4065
    else:
        raise WeasylError("Unexpected")

    d.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%i, %i, %i, %i, %i, %i)",
        [otherid, userid, parentid, commentid, d.get_time(), notiftype])


# notifications
#   3070 stream status later
#   3075 stream status online

def stream_insert(userid, status):
    d.execute("DELETE FROM welcome WHERE otherid = %i AND type IN (3070, 3075)", [userid])

    if status == "n":
        _insert(userid, 0, 0, 3075, followuser.list_followed(userid, "t"))
    elif status == "l":
        _insert(userid, 0, 0, 3070, followuser.list_followed(userid, "t"))


# notifications
#   3010 user followed

def followuser_insert(userid, otherid):
    d.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%i, %i, 0, 0, %i, 3010)",
        [otherid, userid, d.get_time()])


# notifications
#   3010 user followed

def followuser_remove(userid, otherid):
    d.execute("DELETE FROM welcome WHERE (userid, otherid, type) = (%i, %i, 3010)",
              [otherid, userid])


# notifications
#   3080 user requested friendship

def frienduserrequest_insert(tx, *, sender: int, recipient: int) -> None:
    tx.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%(recipient)s, %(sender)s, 0, 0, %(unixtime)s, 3080)",
        recipient=recipient,
        sender=sender,
        unixtime=d.get_time(),
    )


# notifications
#   3080 user requested friendship

def frienduserrequest_remove(tx, *, sender: int, recipient: int) -> None:
    tx.execute(
        "DELETE FROM welcome WHERE (userid, otherid) = (%(recipient)s, %(sender)s) AND type = 3080",
        sender=sender,
        recipient=recipient,
    )


# notifications
#   3085 user accepted friendship

def frienduseraccept_insert(tx, *, requester: int, acceptor: int) -> None:
    tx.execute(
        "INSERT INTO welcome (userid, otherid, referid, targetid, unixtime, type) VALUES (%(requester)s, %(acceptor)s, 0, 0, %(unixtime)s, 3085)",
        requester=requester,
        acceptor=acceptor,
        unixtime=d.get_time(),
    )


# notifications
#   3085 user accepted friendship

def frienduseraccept_remove(tx, *, requester: int, acceptor: int) -> None:
    tx.execute(
        "DELETE FROM welcome WHERE (userid, otherid) = (%(requester)s, %(acceptor)s) AND type = 3085",
        requester=requester,
        acceptor=acceptor,
    )

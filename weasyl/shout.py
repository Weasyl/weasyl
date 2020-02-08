from __future__ import absolute_import

import arrow

from libweasyl import staff

from weasyl import define as d
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import welcome
from weasyl.comment import thread
from weasyl.error import WeasylError


def select(userid, ownerid, limit=None, staffnotes=False):
    statement = ["""
        SELECT
            sh.commentid, sh.parentid, sh.userid, pr.username,
            sh.content, sh.unixtime, sh.settings, sh.indent,
            sh.hidden_by
        FROM comments sh
            INNER JOIN profile pr USING (userid)
        WHERE sh.target_user = %i
            AND sh.settings %s~ 's'
    """ % (ownerid, "" if staffnotes else "!")]

    # moderators get to view hidden comments
    if userid not in staff.MODS:
        statement.append(" AND sh.settings !~ 'h'")

    if userid:
        statement.append(m.MACRO_IGNOREUSER % (userid, "sh"))

    statement.append(" ORDER BY sh.commentid")
    query = d.execute("".join(statement))
    result = thread(query, reverse_top_level=True)

    if limit:
        result = result[:limit]

    media.populate_with_user_media(result)
    return result


def count(ownerid, staffnotes=False):
    db = d.connect()
    sh = d.meta.tables['comments']
    op = '~' if staffnotes else '!~'
    q = (
        d.sa.select([d.sa.func.count()])
        .select_from(sh)
        .where(sh.c.settings.op(op)('s'))
        .where(sh.c.target_user == ownerid))
    (ret,), = db.execute(q)
    return ret


def insert(userid, shout, staffnotes=False):
    # Check invalid content
    if not shout.content:
        raise WeasylError("commentInvalid")
    elif not shout.userid or not d.is_vouched_for(shout.userid):
        raise WeasylError("Unexpected")

    # Determine indent and parentuserid
    if shout.parentid:
        parent = d.engine.execute("SELECT userid, indent FROM comments WHERE commentid = %(parentid)s",
                                  parentid=shout.parentid).first()

        if not parent:
            raise WeasylError("shoutRecordMissing")

        indent = parent.indent + 1
        parentuserid = parent.userid
    else:
        indent, parentuserid = 0, None

    # Check permissions
    if userid not in staff.MODS:
        if ignoreuser.check(shout.userid, userid):
            raise WeasylError("pageOwnerIgnoredYou")
        elif ignoreuser.check(userid, shout.userid):
            raise WeasylError("youIgnoredPageOwner")
        elif ignoreuser.check(parentuserid, userid):
            raise WeasylError("replyRecipientIgnoredYou")
        elif ignoreuser.check(userid, parentuserid):
            raise WeasylError("youIgnoredReplyRecipient")

        settings = d.engine.execute(
            "SELECT lo.settings, pr.config FROM login lo"
            " INNER JOIN profile pr ON lo.userid = pr.userid"
            " WHERE lo.userid = %(target_user)s",
            target_user=shout.userid,
        ).first()

        if "b" in settings[0] or "w" in settings[1] or "x" in settings[1] and not frienduser.check(userid, shout.userid):
            raise WeasylError("insufficientActionPermissions")

    # Create comment
    settings = 's' if staffnotes else ''
    co = d.meta.tables['comments']
    db = d.connect()
    commentid = db.scalar(
        co.insert()
        .values(userid=userid, target_user=shout.userid, parentid=shout.parentid or None, content=shout.content,
                unixtime=arrow.utcnow(), indent=indent, settings=settings)
        .returning(co.c.commentid))

    # Create notification
    if shout.parentid and userid != parentuserid:
        if not staffnotes or parentuserid in staff.MODS:
            welcome.shoutreply_insert(userid, commentid, parentuserid, shout.parentid, staffnotes)
    elif not staffnotes and shout.userid and userid != shout.userid:
        welcome.shout_insert(userid, commentid, otherid=shout.userid)

    d.metric('increment', 'shouts')

    return commentid


def remove(userid, commentid=None):
    query = d.engine.execute(
        "SELECT userid, target_user, settings FROM comments WHERE commentid = %(id)s AND settings !~ 'h'",
        id=commentid,
    ).first()

    if not query or ('s' in query[2] and userid not in staff.MODS):
        raise WeasylError("shoutRecordMissing")

    if userid != query[1] and userid not in staff.MODS:
        if userid != query[0]:
            raise WeasylError("InsufficientPermissions")

        # user is commenter
        replies = d.execute(
            "SELECT commentid FROM comments WHERE parentid = %d", [commentid])
        if replies:
            # a commenter cannot remove their comment if it has replies
            raise WeasylError("InsufficientPermissions")

    # remove notifications
    welcome.comment_remove(commentid, 'shout')
    d._page_header_info.invalidate(userid)

    # hide comment
    d.execute("UPDATE comments SET settings = settings || 'h', hidden_by = %i WHERE commentid = %i", [userid, commentid])

    return query[1]

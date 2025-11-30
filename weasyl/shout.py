import arrow
import sqlalchemy as sa

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
            sh.content, sh.unixtime, sh.settings ~ 'h', sh.hidden_by
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


def count_staff_notes(ownerid):
    db = d.connect()
    sh = d.meta.tables['comments']
    q = (
        sa.select([sa.func.count()])
        .select_from(sh)
        .where(sh.c.settings.op('~')('s'))
        .where(sh.c.target_user == ownerid))
    (ret,), = db.execute(q)
    return ret


def insert(
    userid: int,
    *,
    target_user: int,
    parentid: int,
    content: str,
    staffnotes: bool,
) -> int:
    # Check invalid content
    if not content:
        raise WeasylError("commentInvalid")
    elif not target_user or (not d.is_vouched_for(target_user) and not staffnotes):
        raise WeasylError("Unexpected")

    # Determine parent userid
    if parentid:
        # NOTE: Replying to deleted comments is intentionally allowed.
        parentuserid = d.engine.scalar(
            "SELECT userid FROM comments"
            " WHERE commentid = %(parent)s"
            " AND target_user = %(target)s"
            " AND (settings ~ 's') = %(staffnotes)s",
            parent=parentid,
            target=target_user,
            staffnotes=staffnotes,
        )

        if parentuserid is None:
            raise WeasylError("Unexpected")
    else:
        parentuserid = None

    # Check permissions
    if userid not in staff.MODS:
        if ignoreuser.check(target_user, userid):
            raise WeasylError("pageOwnerIgnoredYou")
        elif ignoreuser.check(userid, target_user):
            raise WeasylError("youIgnoredPageOwner")
        elif ignoreuser.check(parentuserid, userid):
            raise WeasylError("replyRecipientIgnoredYou")
        elif ignoreuser.check(userid, parentuserid):
            raise WeasylError("youIgnoredReplyRecipient")

        is_banned, _ = d.get_login_settings(target_user)
        profile_config = d.get_config(target_user)

        if is_banned or "w" in profile_config or "x" in profile_config and not frienduser.check(userid, target_user):
            raise WeasylError("insufficientActionPermissions")

    # Create comment
    settings = 's' if staffnotes else ''
    co = d.meta.tables['comments']
    db = d.connect()
    commentid = db.scalar(
        co.insert()
        .values(userid=userid, target_user=target_user, parentid=parentid or None, content=content,
                unixtime=arrow.utcnow(), settings=settings)
        .returning(co.c.commentid))

    # Create notification
    if parentid and userid != parentuserid:
        if not staffnotes or parentuserid in staff.MODS:
            welcome.shoutreply_insert(userid, commentid, parentuserid, parentid, staffnotes)
    elif not staffnotes and userid != target_user:
        welcome.shout_insert(userid, commentid, otherid=target_user)

    d.metric('increment', 'shouts')

    return commentid


def remove(userid, *, commentid):
    query = d.engine.execute(
        "SELECT userid, target_user, settings FROM comments WHERE commentid = %(id)s AND target_user IS NOT NULL AND settings !~ 'h'",
        id=commentid,
    ).first()

    if not query or ((is_staff_note := 's' in query[2]) and userid not in staff.MODS):
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

    # Remove notifications. Top-level staff notes don't create notifications. For simplicity, staff note replies aren't removed; mods can see the removed comment anyway.
    if not is_staff_note:
        welcome.comment_remove(commentid, 'shout')

    # hide comment
    d.execute("UPDATE comments SET settings = settings || 'h', hidden_by = %i WHERE commentid = %i AND settings !~ 'h'", [userid, commentid])

    return query[1]

import arrow

from libweasyl import staff
from libweasyl.legacy import UNIXTIME_OFFSET

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import siteupdate
from weasyl import welcome
from weasyl.error import WeasylError


def thread(query, reverse_top_level):
    """
    Get the display order for an iterable of comments.

    Child comments are always in chronological order, but `reverse_top_level`
    controls the order of top-level comments.
    """
    by_parent = {None: (-1, [])}

    for row in query:
        parentid = row[1] or None  # journalcomment and charcomment use 0 instead of NULL
        t = by_parent.get(parentid)

        if t is None:
            # the parent comment isn’t visible to this user
            continue

        parent_indent, siblings = t

        commentid = row[0]

        siblings.append({
            "commentid": commentid,
            "userid": row[2],
            "username": row[3],
            "content": row[4],
            "unixtime": row[5],
            "indent": parent_indent + 1,
            "hidden": row[6],
            "hidden_by": row[7],
        })

        by_parent[commentid] = parent_indent + 1, []

    result = []

    def _add_with_descendants(comments, hidden):
        for c in comments:
            if hidden:
                c["hidden"] = True

            result.append(c)
            _add_with_descendants(by_parent[c["commentid"]][1], c["hidden"])

    _add_with_descendants(
        reversed(by_parent[None][1]) if reverse_top_level else by_parent[None][1],
        hidden=False,
    )

    return result


def select(userid, submitid=None, charid=None, journalid=None, updateid=None):
    is_hidden = "cm.settings ~ 'h'"

    if submitid:
        statement = ["""
            SELECT
                cm.commentid, cm.parentid, cm.userid, pr.username,
                cm.content, cm.unixtime, cm.settings ~ 'h', cm.hidden_by
            FROM comments cm
                INNER JOIN profile pr USING (userid)
            WHERE cm.target_sub = %d
        """ % (submitid,)]
    else:
        unixtime = "cm.unixtime"

        if charid:
            table = "charcomment"
        elif journalid:
            table = "journalcomment"
        elif updateid:
            table = "siteupdatecomment"
            is_hidden = "cm.hidden_at IS NOT NULL"
            unixtime = "EXTRACT(EPOCH FROM cm.created_at)::int8 + %i" % (UNIXTIME_OFFSET,)
        else:
            raise WeasylError("Unexpected")

        statement = ["""
            SELECT
                cm.commentid, cm.parentid, cm.userid, pr.username,
                cm.content, %s, %s, cm.hidden_by
            FROM %s cm
                INNER JOIN profile pr USING (userid)
            WHERE cm.targetid = %i
        """ % (unixtime, is_hidden, table, d.get_targetid(submitid, charid, journalid, updateid))]

    # moderators get to view hidden comments
    if userid not in staff.MODS:
        statement.append(" AND NOT (%s)" % (is_hidden,))

    if userid:
        statement.append(m.MACRO_IGNOREUSER % (userid, "cm"))

    statement.append(" ORDER BY cm.commentid")
    query = d.execute("".join(statement))
    result = thread(query, reverse_top_level=False)
    media.populate_with_user_media(result)
    return result


def insert(userid, submitid=None, charid=None, journalid=None, updateid=None, parentid=None, content=None):
    if submitid:
        table = "comments"
    elif charid:
        table = "charcomment"
    elif journalid:
        table = "journalcomment"
    elif updateid:
        table = "siteupdatecomment"
    else:
        raise WeasylError("Unexpected")

    if not content:
        raise WeasylError("commentInvalid")

    # Determine parent userid
    if parentid:
        parentuserid = d.engine.scalar(
            "SELECT userid FROM {table} WHERE commentid = %(parent)s".format(table=table),
            parent=parentid,
        )

        if parentuserid is None:
            raise WeasylError("Unexpected")
    else:
        if updateid:
            parentid = None  # parentid == 0

        parentuserid = None

    if updateid:
        otherid = d.engine.scalar("SELECT userid FROM siteupdate WHERE updateid = %(update)s", update=updateid)

        if not otherid:
            raise WeasylError("submissionRecordMissing")
    else:
        # Determine the owner of the target
        if submitid:
            otherid = d.engine.scalar("SELECT userid FROM submission WHERE submitid = %i AND not hidden" % (submitid,))
        else:
            otherid = d.engine.scalar(
                "SELECT userid FROM %s WHERE %s = %i AND settings !~ 'h'" % (
                    ("character", "charid", charid) if charid else
                    ("journal", "journalid", journalid)
                )
            )

        # Check permissions
        if not otherid:
            raise WeasylError("submissionRecordMissing")
        elif ignoreuser.check(otherid, userid):
            raise WeasylError("pageOwnerIgnoredYou")
        elif ignoreuser.check(userid, otherid):
            raise WeasylError("youIgnoredPageOwner")

    if parentuserid and ignoreuser.check(parentuserid, userid):
        raise WeasylError("replyRecipientIgnoredYou")
    elif parentuserid and ignoreuser.check(userid, parentuserid):
        raise WeasylError("youIgnoredReplyRecipient")

    # Create comment
    if submitid:
        co = d.meta.tables['comments']
        db = d.connect()
        commentid = db.scalar(
            co.insert()
            .values(userid=userid, target_sub=submitid, parentid=parentid or None,
                    content=content, unixtime=arrow.utcnow())
            .returning(co.c.commentid))
    elif updateid:
        commentid = d.engine.scalar(
            "INSERT INTO siteupdatecomment (userid, targetid, parentid, content)"
            " VALUES (%(user)s, %(update)s, %(parent)s, %(content)s)"
            " RETURNING commentid",
            user=userid,
            update=updateid,
            parent=parentid,
            content=content,
        )
        siteupdate.select_last.invalidate()
    else:
        commentid = d.engine.scalar(
            "INSERT INTO {table} (userid, targetid, parentid, content, unixtime)"
            " VALUES (%(user)s, %(target)s, %(parent)s, %(content)s, %(now)s)"
            " RETURNING commentid".format(table="charcomment" if charid else "journalcomment"),
            user=userid,
            target=d.get_targetid(charid, journalid),
            parent=parentid or 0,
            content=content,
            now=d.get_time(),
        )

    # Create notification
    if parentid and (userid != parentuserid):
        welcome.commentreply_insert(userid, commentid, parentuserid, parentid, submitid, charid, journalid, updateid)
    elif not parentid:
        # build a list of people this comment should notify
        # circular imports are cool and fun
        from weasyl.collection import find_owners
        notified = set(find_owners(submitid))

        # check to see who we should deliver comment notifications to
        def can_notify(other):
            other_jsonb = d.get_profile_settings(other)
            allow_notify = other_jsonb.allow_collection_notifs
            ignored = ignoreuser.check(other, userid)
            return allow_notify and not ignored
        notified = set(filter(can_notify, notified))
        # always give notification on own content
        notified.add(otherid)
        # don't give me a notification for my own comment
        notified.discard(userid)

        for other in notified:
            welcome.comment_insert(userid, commentid, other, submitid, charid, journalid, updateid)

    d.metric('increment', 'comments')

    return commentid


def remove(userid, feature=None, commentid=None):
    if feature not in ["submit", "char", "journal", "siteupdate"]:
        raise WeasylError("Unexpected")

    if feature == 'submit':
        query = d.engine.execute(
            "SELECT userid, target_sub FROM comments WHERE commentid = %(comment)s AND target_sub IS NOT NULL AND settings !~ 'h'",
            comment=commentid,
        ).first()
    elif feature == 'siteupdate':
        query = d.engine.execute(
            "SELECT userid, targetid FROM siteupdatecomment WHERE commentid = %(comment)s AND hidden_at IS NULL",
            comment=commentid,
        ).first()
    else:
        query = d.engine.execute(
            "SELECT userid, targetid FROM {feature}comment WHERE commentid = %(comment)s AND settings !~ 'h'".format(feature=feature),
            comment=commentid,
        ).first()

    if not query:
        raise WeasylError("RecordMissing")

    target_table = {
        "submit": "submission",
        "char": "character",
        "journal": "journal",
    }

    if feature == 'siteupdate':
        is_owner = False
    else:
        owner = d.engine.scalar(
            "SELECT userid FROM {table} WHERE {feature}id = %(target)s".format(table=target_table[feature], feature=feature),
            target=query[1],
        )
        is_owner = userid == owner

    if not is_owner and userid not in staff.MODS:
        if userid != query[0]:
            raise WeasylError('InsufficientPermissions')

        # user is commenter
        comment_table = (
            "comments" if feature == 'submit' else feature + "comment")
        comment_visible = (
            "hidden_at IS NULL" if feature == 'siteupdate' else "settings !~ 'h'")
        has_replies = d.engine.scalar(
            f"SELECT EXISTS (SELECT FROM {comment_table} WHERE parentid = %(comment)s AND {comment_visible})",
            comment=commentid)
        if has_replies:
            # a commenter cannot remove their comment if it has replies
            raise WeasylError("InsufficientPermissions")

    # remove notifications
    welcome.comment_remove(commentid, feature)
    d._page_header_info.invalidate(userid)

    # mark comments as hidden
    if feature == 'submit':
        d.engine.execute(
            "UPDATE comments SET settings = settings || 'h', hidden_by = %(hidden_by)s WHERE commentid = %(comment)s",
            comment=commentid,
            hidden_by=userid,
        )
    elif feature == 'siteupdate':
        d.engine.execute(
            "UPDATE siteupdatecomment SET hidden_at = now(), hidden_by = %(hidden_by)s WHERE commentid = %(comment)s",
            comment=commentid,
            hidden_by=userid,
        )
        siteupdate.select_last.invalidate()
    else:
        d.engine.execute(
            "UPDATE {feature}comment SET settings = settings || 'h', hidden_by = %(hidden_by)s WHERE commentid = %(comment)s".format(feature=feature),
            comment=commentid,
            hidden_by=userid,
        )

    return query[1]


def count(id, contenttype='submission'):
    """Fetches the count of comments on some content.

    Args:
        id (int): ID of the content to get the count for.
        contenttype (str): Type of content to fetch. It accepts one of the following:
            submission, journal, or character

    Returns:
        An int with the number of comments.
    """

    if contenttype == 'submission':
        return d.engine.scalar(
            'SELECT COUNT(*) FROM comments cm WHERE cm.target_sub = %s',
            (id,))
    elif contenttype == 'journal':
        tablename = 'journalcomment'
    elif contenttype == 'character':
        tablename = 'charcomment'
    else:
        raise ValueError("type should be one of 'submission', 'journal', or 'character'")

    return d.engine.scalar(
        'SELECT COUNT(*) FROM {table} cm WHERE cm.targetid = %s'.format(table=tablename),
        (id,))

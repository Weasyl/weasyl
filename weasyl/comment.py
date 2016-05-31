# content.py

import arrow

from libweasyl import staff

from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


_MAX_LEVEL = 8
_PER_LEVEL = 50


def _thread(query, result, i):
    parent = result[-1]
    for j in range(i + 1, len(query)):
        # comment row j is a child of i
        if query[j][1] == query[i][0]:
            result.append({
                "commentid": query[j][0],
                "parentid": query[j][1],
                "userid": query[j][2],
                "username": query[j][3],
                "status": "".join(i for i in query[j][4] if i in "bs"),
                "content": query[j][5],
                "unixtime": query[j][6],
                "settings": query[j][7],
                "indent": query[j][8],
                "hidden": parent["hidden"] or 'h' in query[j][7],
                "hidden_by": query[j][10],
            })

            _thread(query, result, j)


def select(userid, submitid=None, charid=None, journalid=None):
    result = []

    if submitid:
        statement = ["""
            SELECT
                cm.commentid, cm.parentid, cm.userid, pr.username, lo.settings,
                cm.content, cm.unixtime, cm.settings, cm.indent, pr.config,
                cm.hidden_by
            FROM comments cm
            INNER JOIN profile pr USING (userid)
            INNER JOIN login lo USING (userid)
            WHERE cm.target_sub = %d
        """ % (submitid,)]
    else:
        statement = ["""
            SELECT
                cm.commentid, cm.parentid, cm.userid, pr.username, lo.settings, cm.content, cm.unixtime, cm.settings,
                cm.indent, pr.config, cm.hidden_by
            FROM %scomment cm
                INNER JOIN profile pr USING (userid)
                INNER JOIN login lo USING (userid)
            WHERE cm.targetid = %i
        """ % ("submit" if submitid else "char" if charid else "journal", d.get_targetid(submitid, charid, journalid))]

    # moderators get to view hidden comments
    if userid not in staff.MODS:
        statement.append(" AND cm.settings !~ 'h'")

    if userid:
        statement.append(m.MACRO_IGNOREUSER % (userid, "cm"))

    statement.append(" ORDER BY COALESCE(cm.parentid, 0), cm.unixtime")
    query = d.execute("".join(statement))

    for i, comment in enumerate(query):
        if comment[1]:
            break

        result.append({
            "commentid": comment[0],
            "parentid": comment[1],
            "userid": comment[2],
            "username": comment[3],
            "status": "".join({"b", "s"} & set(comment[4])),
            "content": comment[5],
            "unixtime": comment[6],
            "settings": comment[7],
            "indent": comment[8],
            "hidden": 'h' in comment[7],
            "hidden_by": comment[10],
        })

        _thread(query, result, i)

    media.populate_with_user_media(result)
    return result


# TODO(kailys): use ORM argument after comment tables are merged.
def insert(userid, submitid=None, charid=None, journalid=None, parentid=None, content=None):
    if not submitid and not charid and not journalid:
        raise WeasylError("Unexpected")
    elif not content:
        raise WeasylError("commentInvalid")

    # Determine indent and parentuserid
    if parentid:
        query = d.execute("SELECT userid, indent FROM %s WHERE commentid = %i",
                          ["comments" if submitid else "charcomment" if charid else "journalcomment", parentid],
                          options="single")

        if not query:
            raise WeasylError("Unexpected")

        indent = query[1] + 1
        parentuserid = query[0]
    else:
        indent = 0
        parentuserid = None

    # Determine otherid
    otherid = d.execute("SELECT userid FROM %s WHERE %s = %i AND settings !~ 'h'",
                        ["submission", "submitid", submitid] if submitid else
                        ["character", "charid", charid] if charid else
                        ["journal", "journalid", journalid], options="element")

    # Check permissions
    if not otherid:
        raise WeasylError("submissionRecordMissing")
    elif ignoreuser.check(otherid, userid):
        raise WeasylError("pageOwnerIgnoredYou")
    elif ignoreuser.check(userid, otherid):
        raise WeasylError("youIgnoredPageOwner")
    elif parentuserid and ignoreuser.check(parentuserid, userid):
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
                    content=content, unixtime=arrow.utcnow(), indent=indent)
            .returning(co.c.commentid))
    else:
        commentid = d.execute(
            "INSERT INTO %s (userid, targetid, parentid, "
            "content, unixtime, indent) VALUES (%i, %i, %i, '%s', %i, %i) RETURNING "
            "commentid", [
                "charcomment" if charid else "journalcomment", userid,
                d.get_targetid(submitid, charid, journalid),
                parentid, content, d.get_time(), indent
            ], options="element")

    # Create notification
    if parentid and (userid != parentuserid):
        welcome.commentreply_insert(userid, commentid, parentuserid, parentid, submitid, charid, journalid)
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
            welcome.comment_insert(userid, commentid, other, submitid, charid, journalid)

    d.metric('increment', 'comments')

    return commentid


# form
#   content
#   commentid
#   feature

# NOTE: This method is UNUSED.
def edit(userid, form):
    commentid = d.get_int(form.commentid)

    if form.feature not in ["submit", "char", "journal"]:
        raise WeasylError("Unexpected")

    query = d.execute("SELECT userid, unixtime FROM %scomment WHERE commentid = %i AND settings !~ 'h'",
                      [form.feature, commentid], options="single")

    if not query:
        raise WeasylError("RecordMissing")
    elif userid != query[0] and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    elif query[1] < d.get_time() - 600:
        raise WeasylError("TimeLimitExceeded")

    d.execute("UPDATE %scomment SET content = '%s' WHERE commentid = %i",
              [form.feature, form.content.strip(), commentid])


def remove(userid, feature=None, commentid=None):

    if feature not in ["submit", "char", "journal"]:
        raise WeasylError("Unexpected")

    if feature == 'submit':
        query = d.execute(
            "SELECT userid, target_sub FROM comments WHERE commentid = %i AND settings !~ 'h'",
            [commentid], ["single"])
    else:
        query = d.execute(
            "SELECT userid, targetid FROM %scomment WHERE commentid = %i AND settings !~ 'h'",
            [feature, commentid], ["single"])

    if not query or query[1] is None:
        raise WeasylError("RecordMissing")

    target_table = {
        "submit": "submission",
        "char": "character",
        "journal": "journal",
    }

    owner = d.execute(
        "SELECT userid FROM %s WHERE %sid = %i",
        [target_table[feature], feature, query[1]], ["single"])
    is_owner = userid == owner[0]

    if not is_owner and userid not in staff.MODS:
        if userid != query[0]:
            raise WeasylError('InsufficientPermissions')

        # user is commenter
        comment_table = (
            "comments" if feature == 'submit' else feature + "comment")
        replies = d.execute(
            "SELECT commentid FROM %s WHERE parentid = %d",
            [comment_table, commentid])
        if replies:
            # a commenter cannot remove their comment if it has replies
            raise WeasylError("InsufficientPermissions")

    # remove notifications
    welcome.comment_remove(commentid, feature)
    d._page_header_info.invalidate(userid)

    # mark comments as hidden
    if feature == 'submit':
        d.execute(
            "UPDATE comments SET settings = settings || 'h', hidden_by = %i WHERE commentid = %i",
            [userid, commentid])
    else:
        d.execute(
            "UPDATE %scomment SET settings = settings || 'h', hidden_by = %i WHERE commentid = %i",
            [feature, userid, commentid])

    return query[1]


def count(submitid=None, journalid=None, charid=None):
    # TODO(kailys): refactor to not select from media table
    return len(select(0, submitid=submitid, journalid=journalid, charid=charid))

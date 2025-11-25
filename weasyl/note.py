import arrow

from libweasyl import staff

from weasyl import define as d
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl.error import WeasylError
from weasyl.forms import parse_sysname_list


"""
In this module, ps is the alias for the table joined to the message sender,
while pr is the alias for the table joined to the message recipient. Similarly,
ms.userid refers to the user who sent the message, while ms.otherid is the
user who received it.
"""


PAGE_SIZE = 50
COUNT_LIMIT = 1000


def _select_inbox_query(with_backid: bool, with_nextid: bool, with_filter: bool):
    yield """
        FROM message ms
            INNER JOIN profile ps USING (userid)
        WHERE ms.otherid = %(recipient)s
            AND ms.settings !~ 'r'
    """

    if with_filter:
        yield " AND ms.userid = ANY (%(filter)s)"

    if with_backid:
        yield " AND ms.noteid > %(backid)s"
    elif with_nextid:
        yield " AND ms.noteid < %(nextid)s"


def _select_outbox_query(with_backid: bool, with_nextid: bool, with_filter: bool):
    yield """
        FROM message ms
            INNER JOIN profile pr ON ms.otherid = pr.userid
        WHERE ms.userid = %(sender)s
            AND ms.settings !~ 's'
    """

    if with_filter:
        yield " AND ms.otherid = ANY (%(filter)s)"

    if with_backid:
        yield " AND ms.noteid > %(backid)s"
    elif with_nextid:
        yield " AND ms.noteid < %(nextid)s"


def select_inbox(userid, *, limit: None, backid, nextid, filter):
    statement = "".join((
        "SELECT ms.noteid, ms.userid, ps.username, ms.title, ms.unixtime, ms.settings",
        *_select_inbox_query(
            with_backid=backid is not None,
            with_nextid=nextid is not None,
            with_filter=bool(filter),
        ),
        f" ORDER BY ms.noteid {'DESC' if backid is None else ''} LIMIT {PAGE_SIZE}",
    ))

    query = [{
        "noteid": i.noteid,
        "senderid": i.userid,
        "sendername": i.username,
        "unread": "u" in i.settings,
        "title": i.title,
        "unixtime": i.unixtime,
    } for i in d.engine.execute(
        statement, recipient=userid, filter=filter, backid=backid, nextid=nextid)]

    return query if backid is None else query[::-1]


def select_outbox(userid, *, limit: None, backid, nextid, filter):
    statement = "".join((
        "SELECT ms.noteid, ms.otherid, pr.username, ms.title, ms.unixtime",
        *_select_outbox_query(
            with_backid=backid is not None,
            with_nextid=nextid is not None,
            with_filter=bool(filter),
        ),
        f" ORDER BY ms.noteid {'DESC' if backid is None else ''} LIMIT {PAGE_SIZE}",
    ))

    query = [{
        "noteid": i.noteid,
        "recipientid": i.otherid,
        "recipientname": i.username,
        "title": i.title,
        "unixtime": i.unixtime,
    } for i in d.engine.execute(
        statement, sender=userid, filter=filter, backid=backid, nextid=nextid)]

    return query if backid is None else query[::-1]


def select_inbox_count(userid, *, backid, nextid, filter):
    statement = "".join((
        "SELECT count(*) FROM (SELECT ",
        *_select_inbox_query(
            with_backid=backid is not None,
            with_nextid=nextid is not None,
            with_filter=bool(filter),
        ),
        f" LIMIT {COUNT_LIMIT}) t",
    ))
    return d.engine.scalar(
        statement, recipient=userid, filter=filter, backid=backid, nextid=nextid)


def select_outbox_count(userid, *, backid, nextid, filter):
    statement = "".join((
        "SELECT count(*) FROM (SELECT ",
        *_select_outbox_query(
            with_backid=backid is not None,
            with_nextid=nextid is not None,
            with_filter=bool(filter),
        ),
        f" LIMIT {COUNT_LIMIT}) t",
    ))
    return d.engine.scalar(
        statement, sender=userid, filter=filter, backid=backid, nextid=nextid)


def select_view(userid, noteid):
    query = d.engine.execute(
        "SELECT ps.userid, ps.username, pr.userid, pr.username, "
        "ms.title, ms.content, ms.unixtime, ms.settings FROM message ms INNER "
        "JOIN profile ps ON ms.userid = ps.userid INNER JOIN profile pr ON "
        "ms.otherid = pr.userid WHERE ms.noteid = %(id)s",
        id=noteid,
    ).first()

    if not query:
        raise WeasylError("noteRecordMissing")
    elif userid == query[0] and "s" in query[7]:
        raise WeasylError("noteRecordMissing")
    elif userid == query[2] and "r" in query[7]:
        raise WeasylError("noteRecordMissing")
    elif userid not in [query[0], query[2]]:
        raise WeasylError("InsufficientPermissions")

    if query[2] == userid and "u" in query[7]:
        d.execute("UPDATE message SET settings = REPLACE(settings, 'u', '') WHERE noteid = %i", [noteid])
        d._page_header_info.invalidate(userid)

    return {
        "noteid": noteid,
        "senderid": query[0],
        "mine": userid == query[0],
        "sendername": query[1],
        "recipientid": query[2],
        "recipientname": query[3],
        "title": query[4],
        "content": query[5],
        "unixtime": query[6],
    }


# form
#   title
#   content
#   recipient

def send(userid, form):
    form.title = form.title.strip()
    form.content = form.content.strip()

    if not form.content:
        raise WeasylError("contentInvalid")
    elif not form.title:
        raise WeasylError("titleInvalid")
    elif len(form.title) > 100:
        raise WeasylError("titleTooLong")

    recipient_sysnames = parse_sysname_list(form.recipient)
    if len(recipient_sysnames) > 1:
        raise WeasylError("recipientExcessive")

    recipientids = d.get_userids(recipient_sysnames)
    if not recipientids:
        raise WeasylError("recipientInvalid")

    [recipientid] = recipientids.values()
    del recipient_sysnames, recipientids

    # can't send a note to yourself
    if recipientid == userid:
        raise WeasylError("recipientInvalid")

    # can't send a note to a user who ignores you
    if ignoreuser.check(recipientid, userid):
        raise WeasylError("recipientInvalid")

    # can't send a note to an unverified user
    if not d.is_vouched_for(recipientid):
        raise WeasylError("recipientInvalid")

    # can't send a note to a user you're ignoring
    if ignoreuser.check(userid, recipientid):
        raise WeasylError("recipientInvalid")

    if userid not in staff.MODS:
        recipient_config = d.get_config(recipientid)

        def is_permitted_sender():
            return d.engine.scalar(
                "SELECT EXISTS (SELECT FROM permitted_senders WHERE (userid, sender) = (%(recipient)s, %(user)s))",
                recipient=recipientid,
                user=userid,
            )

        # Staff notes only
        if "y" in recipient_config and not is_permitted_sender():
            raise WeasylError("recipientInvalid")

        # Friend notes only
        if "z" in recipient_config and not frienduser.check(userid, recipientid) and not is_permitted_sender():
            raise WeasylError("recipientInvalid")

    d.engine.execute(
        "INSERT INTO message (userid, otherid, title, content, unixtime)"
        " VALUES (%(sender)s, %(recipient)s, %(title)s, %(content)s, %(now)s)",
        sender=userid,
        title=form.title,
        content=form.content,
        now=d.get_time(),
        recipient=recipientid,
    )

    d._page_header_info.invalidate(recipientid)

    d.engine.execute(
        """
        INSERT INTO permitted_senders (userid, sender)
            VALUES (%(user)s, %(recipient)s)
            ON CONFLICT (userid, sender) DO NOTHING
        """,
        user=userid,
        recipient=recipientid,
    )

    if form.mod_copy and userid in staff.MODS:
        mod_content = (
            '## The following message was sent as a note to the user.\n\n### %s\n\n%s' % (
                form.title, form.content))
        if form.staff_note:
            mod_content = '%s\n\n%s' % (form.staff_note, mod_content)
        now = arrow.utcnow()
        d.engine.execute(
            d.meta.tables['comments'].insert()
            .values({
                'userid': userid,
                'target_user': recipientid,
                'unixtime': now,
                'settings': 's',
                'content': mod_content,
            }))


def remove_list(userid, noteids):
    if not noteids:
        return

    # Add "sender trashed" (s) to requested notes that the user sent
    d.engine.execute(
        "UPDATE message SET settings = settings || 's' WHERE noteid = ANY (%(ids)s) AND userid = %(user)s AND settings !~ 's'",
        user=userid,
        ids=noteids,
    )

    # Remove "unread" (u) from and add "recipient trashed" (r) to requested notes that the user received
    d.engine.execute(
        "UPDATE message SET settings = REPLACE(settings, 'u', '') || 'r' WHERE noteid = ANY (%(ids)s) AND otherid = %(user)s AND settings !~ 'r'",
        user=userid,
        ids=noteids,
    )


unread_count = d.private_messages_unread_count

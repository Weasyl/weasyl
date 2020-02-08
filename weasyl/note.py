from __future__ import absolute_import

import arrow

from libweasyl import staff

from weasyl import define as d
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl.error import WeasylError


"""
In this module, ps is the alias for the table joined to the message sender,
while pr is the alias for the table joined to the message recipient. Similarly,
ms.userid refers to the user who sent the message, while ms.otherid is the
user who received it.
"""


def select_inbox(userid, limit, backid=None, nextid=None, filter=[]):
    statement = ["""
        SELECT ms.noteid, ms.userid, ps.username, ms.title, ms.unixtime, ms.settings
        FROM message ms
            INNER JOIN profile ps USING (userid)
        WHERE (ms.otherid, ms.other_folder) = (%(recipient)s, 0)
            AND ms.settings !~ 'r'
    """]

    if filter:
        statement.append(" AND ms.userid = ANY (%(filter)s)")

    if backid:
        statement.append(" AND ms.noteid > %(backid)s ORDER BY ms.noteid")
    elif nextid:
        statement.append(" AND ms.noteid < %(nextid)s ORDER BY ms.noteid DESC")
    else:
        statement.append(" ORDER BY ms.noteid DESC")

    statement.append(" LIMIT %(limit)s")

    query = [{
        "noteid": i.noteid,
        "senderid": i.userid,
        "sendername": i.username,
        "unread": "u" in i.settings,
        "title": i.title,
        "unixtime": i.unixtime,
    } for i in d.engine.execute(
        "".join(statement), recipient=userid, filter=filter, backid=backid, nextid=nextid, limit=limit)]

    return list(reversed(query)) if backid else query


def select_outbox(userid, limit, backid=None, nextid=None, filter=[]):
    statement = ["""
        SELECT ms.noteid, ms.otherid, pr.username, ms.title, ms.unixtime
        FROM message ms
            INNER JOIN profile pr ON ms.otherid = pr.userid
        WHERE (ms.userid, ms.user_folder) = (%(sender)s, 0)
            AND ms.settings !~ 's'
    """]

    if filter:
        statement.append(" AND ms.otherid = ANY (%(filter)s)")

    if backid:
        statement.append(" AND ms.noteid > %(backid)s ORDER BY ms.noteid")
    elif nextid:
        statement.append(" AND ms.noteid < %(nextid)s ORDER BY ms.noteid DESC")
    else:
        statement.append(" ORDER BY ms.noteid DESC")

    statement.append(" LIMIT %(limit)s")

    query = [{
        "noteid": i.noteid,
        "recipientid": i.otherid,
        "recipientname": i.username,
        "title": i.title,
        "unixtime": i.unixtime,
    } for i in d.engine.execute(
        "".join(statement), sender=userid, filter=filter, backid=backid, nextid=nextid, limit=limit)]

    return list(reversed(query)) if backid else query


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

    users = set(d.get_userid_list(form.recipient))

    # can't send a note to yourself
    users.discard(userid)

    # can't send a note to a user who ignores you
    users.difference_update(
        d.column(d.engine.execute("SELECT userid FROM ignoreuser WHERE otherid = %(user)s", user=userid)))

    # can't send a note to an unverified user
    users.difference_update(
        d.column(d.engine.execute("SELECT userid FROM login WHERE userid = ANY (%(users)s) AND voucher IS NULL", users=list(users))))

    # can't send a note to a user you're ignoring
    users.difference_update(ignoreuser.cached_list_ignoring(userid))

    if not users:
        raise WeasylError("recipientInvalid")

    configs = d.engine.execute(
        "SELECT userid, config FROM profile WHERE userid = ANY (%(recipients)s)",
        recipients=list(users)).fetchall()

    if userid not in staff.MODS:
        ignore_global_restrictions = {i for (i,) in d.engine.execute(
            "SELECT userid FROM permitted_senders WHERE sender = %(user)s",
            user=userid)}

        remove = (
            # Staff notes only
            {j[0] for j in configs if "y" in j[1]} |
            # Friend notes only
            {j[0] for j in configs if "z" in j[1] and not frienduser.check(userid, j[0])}
        )

        users.difference_update(remove - ignore_global_restrictions)

    if not users:
        raise WeasylError("recipientInvalid")
    elif len(users) > 10:
        raise WeasylError("recipientExcessive")

    d.engine.execute(
        "INSERT INTO message (userid, otherid, title, content, unixtime)"
        " SELECT %(sender)s, recipient, %(title)s, %(content)s, %(now)s"
        " FROM UNNEST (%(recipients)s) AS recipient",
        sender=userid,
        title=form.title,
        content=form.content,
        now=d.get_time(),
        recipients=list(users),
    )

    for u in users:
        d._page_header_info.invalidate(u)

    d.engine.execute(
        """
        INSERT INTO permitted_senders (userid, sender)
            SELECT %(user)s, sender FROM UNNEST (%(recipients)s) AS sender
            ON CONFLICT (userid, sender) DO NOTHING
        """,
        user=userid,
        recipients=list(users),
    )

    if form.mod_copy and userid in staff.MODS:
        mod_content = (
            '## The following message was sent as a note to the user.\n\n### %s\n\n%s' % (
                form.title, form.content))
        if form.staff_note:
            mod_content = '%s\n\n%s' % (form.staff_note, mod_content)
        now = arrow.utcnow()
        mod_copies = []
        for target in users:
            mod_copies.append({
                'userid': userid,
                'target_user': target,
                'unixtime': now,
                'settings': 's',
                'content': mod_content,
            })
        d.engine.execute(
            d.meta.tables['comments'].insert()
            .values(mod_copies))


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

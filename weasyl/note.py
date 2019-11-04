from __future__ import absolute_import

import arrow

from libweasyl import staff

from weasyl import define as d
from weasyl import frienduser
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

    users = set(i for i in d.get_userid_list(form.recipient) if i != userid)
    users.difference_update(
        d.execute("SELECT userid FROM ignoreuser WHERE otherid = %i", [userid], option="within"))
    users.difference_update(
        d.execute("SELECT otherid FROM ignoreuser WHERE userid = %i", [userid], option="within"))
    if not users:
        raise WeasylError("recipientInvalid")

    configs = d.execute(
        "SELECT userid, config FROM profile WHERE userid IN %s",
        [d.sql_number_list(list(users))])

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

    argv = []
    unixtime = d.get_time()
    statement = ["INSERT INTO message (userid, otherid, title, content, unixtime) VALUES"]

    for i in users:
        argv.extend([form.title, form.content])
        statement.append(" (%i, %i, '%%s', '%%s', %i)," % (userid, i, unixtime))
        d._page_header_info.invalidate(i)

    statement[-1] = statement[-1][:-1]
    d.execute("".join(statement), argv)

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


# form
#   noteid
#   folderid

def move(userid, form):
    noteid = d.get_int(form.noteid)
    folderid = d.get_int(form.folderid)
    query = d.engine.execute("SELECT userid, otherid, settings FROM message WHERE noteid = %(id)s", id=noteid).first()

    if not query:
        raise WeasylError("Unexpected")
    elif userid not in query:
        raise WeasylError("Unexpected")
    elif userid == query[0] and "s" in query[2]:
        raise WeasylError("Unexpected")
    elif userid == query[1] and "r" in query[2]:
        raise WeasylError("Unexpected")
    elif not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM messagefolder WHERE (folderid, userid) = (%(folder)s, %(user)s))",
                             folder=folderid, user=userid):
        raise WeasylError("Unexpected")

    d.execute("UPDATE message SET %s_folder = %i WHERE noteid = %i",
              ["user" if userid == query[0] else "other", folderid, noteid])


def remove_list(userid, noteids):
    if not noteids:
        return

    rem_sent = []
    rem_received = []

    query = d.execute("SELECT userid, otherid, settings, noteid FROM message WHERE noteid IN %s",
                      [d.sql_number_list(noteids)])

    for i in query:
        if i[0] == userid and "s" not in i[2]:
            rem_sent.append(i[3])
        if i[1] == userid and "r" not in i[2]:
            rem_received.append(i[3])

    if rem_sent:
        d.execute("UPDATE message SET settings = settings || 's' WHERE noteid IN %s", [d.sql_number_list(rem_sent)])

    if rem_received:
        d.execute("UPDATE message SET settings = REPLACE(settings, 'u', '') || 'r' WHERE noteid IN %s",
                  [d.sql_number_list(rem_received)])


def remove(userid, noteid):
    query = d.engine.execute("SELECT userid, otherid, settings FROM message WHERE noteid = %(id)s", id=noteid).first()

    if not query:
        raise WeasylError("Unexpected")
    elif userid not in query:
        raise WeasylError("Unexpected")
    elif userid == query[0] and "s" in query[2]:
        raise WeasylError("Unexpected")
    elif userid == query[1] and "r" in query[2]:
        raise WeasylError("Unexpected")

    if userid == query[1] and "u" in query[2]:
        d.execute("UPDATE message SET settings = REPLACE(settings, 'u', '') || 'r' WHERE noteid = %i", [noteid])
    else:
        d.execute("UPDATE message SET settings = settings || '%s' WHERE noteid = %i",
                  ["s" if userid == query[0] else "r", noteid])

from __future__ import absolute_import

import arrow
import sqlalchemy as sa

from libweasyl import staff
from libweasyl.legacy import UNIXTIME_OFFSET

from weasyl import define as d
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


_TITLE = 100


def create(userid, form):
    form.title = form.title.strip()[:_TITLE]
    form.content = form.content.strip()

    if not form.title:
        raise WeasylError("titleInvalid")
    elif not form.content:
        raise WeasylError("titleInvalid")
    elif userid not in staff.ADMINS:
        raise WeasylError("InsufficientPermissions")

    su = d.meta.tables['siteupdate']
    q = (
        su.insert()
        .values(userid=userid, title=form.title, content=form.content, unixtime=arrow.utcnow())
        .returning(su.c.updateid))
    db = d.connect()
    updateid = db.scalar(q)
    welcome.site_update_insert(updateid)


def edit(userid, form):
    form.title = form.title.strip()[:_TITLE]
    form.content = form.content.strip()

    if not form.title:
        raise WeasylError("titleInvalid")
    elif not form.content:
        raise WeasylError("titleInvalid")
    elif not form.siteupdateid:
        raise WeasylError("titleInvalid")
    elif userid not in staff.ADMINS:
        raise WeasylError("InsufficientPermissions")

    d.engine.execute("""
        UPDATE siteupdate
        SET title = %(title)s, content = %(content)s
        WHERE updateid = %(updateid)s
    """, title=form.title, content=form.content, updateid=form.siteupdateid)


def select(limit=1):
    ret = [{
        "updateid": i[0],
        "userid": i[1],
        "username": i[2],
        "title": i[3],
        "content": i[4],
        "unixtime": i[5],
    } for i in d.execute("""
        SELECT up.updateid, up.userid, pr.username, up.title, up.content, up.unixtime, pr.config
        FROM siteupdate up
            INNER JOIN profile pr USING (userid)
        ORDER BY updateid DESC
        LIMIT %i
    """, [limit])]

    media.populate_with_user_media(ret)
    return ret


def select_by_id(updateid):
    su = d.meta.tables['siteupdate']
    pr = d.meta.tables['profile']
    q = (
        sa.select([
            pr.c.userid, pr.c.username, su.c.title, su.c.content, su.c.unixtime,
        ])
        .select_from(su.join(pr, su.c.userid == pr.c.userid))
        .where(su.c.updateid == updateid))
    db = d.connect()
    results = db.execute(q).fetchall()
    if not results:
        raise WeasylError('RecordMissing')
    results = dict(results[0])
    results['user_media'] = media.get_user_media(results['userid'])
    results['timestamp'] = results['unixtime'].timestamp + UNIXTIME_OFFSET
    return results

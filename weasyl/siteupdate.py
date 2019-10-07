from __future__ import absolute_import

import arrow

from libweasyl import staff
from libweasyl.models.site import SiteUpdate
from weasyl import define as d
from weasyl import media
from weasyl import welcome


def create(userid, title, content, wesley=False):
    update = SiteUpdate(
        userid=userid,
        wesley=wesley,
        title=title,
        content=content,
        unixtime=arrow.utcnow(),
    )

    SiteUpdate.dbsession.add(update)
    SiteUpdate.dbsession.flush()
    welcome.site_update_insert(update.updateid)

    return update


def select_last():
    last = d.engine.execute("""
        SELECT
            up.updateid, pr.userid, pr.username, up.title, up.content, up.unixtime,
            (SELECT count(*) FROM siteupdatecomment c WHERE c.targetid = up.updateid) AS comment_count
        FROM siteupdate up
            LEFT JOIN profile pr ON pr.userid = CASE WHEN up.wesley THEN %(wesley)s ELSE up.userid END
        ORDER BY updateid DESC
        LIMIT 1
    """, wesley=staff.WESLEY).first()

    if not last:
        return None

    return dict(last, user_media=media.get_user_media(last.userid))

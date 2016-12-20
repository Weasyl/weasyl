from __future__ import absolute_import

import arrow

from libweasyl.models.site import SiteUpdate
from weasyl import define as d
from weasyl import media
from weasyl import welcome


def create(userid, title, content):
    update = SiteUpdate(
        userid=userid,
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
        SELECT up.updateid, up.userid, pr.username, up.title, up.content, up.unixtime
        FROM siteupdate up
            INNER JOIN profile pr USING (userid)
        ORDER BY updateid DESC
        LIMIT 1
    """).first()

    if not last:
        return None

    return dict(last, user_media=media.get_user_media(last.userid))

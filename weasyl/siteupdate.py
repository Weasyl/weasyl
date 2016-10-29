from __future__ import absolute_import

from weasyl import define as d
from weasyl import media


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

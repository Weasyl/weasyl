import os
import random
import time

from datetime import datetime
from libweasyl.files import fanout
from libweasyl.models.media import fetch_or_create_media_item
from weasyl import image
from weasyl.define import engine, region
from weasyl.error import WeasylError


class Ad(object):
    def __init__(self, link_target, start, end, image_path):
        self.link_target = link_target
        self.start = start
        self.end = end
        self.image_path = image_path


PERMITTED_TYPES = {"jpg", "png"}
SIZE_LIMIT = 200 * 1024  # 200 KB


def _serializable_datetime(dt):
    if dt is None:
        return None

    return int(time.mktime(dt.timetuple()))


def _from_row(row):
    filename = "%s.%s" % (row.sha256, row.file_type)

    return {
        "link_target": row.link_target,
        "start": _serializable_datetime(row.start),
        "end": _serializable_datetime(row.end),
        "image_path": os.path.join(
            "/static/media",
            *fanout(row.sha256, [2, 2, 2]) + [filename]),
    }


@region.cache_on_arguments()
def _get_all_ads():
    all_ads = engine.execute("""
        SELECT ads.link_target, ads.start, ads.end, media.sha256, media.file_type
        FROM ads
            INNER JOIN media ON ads.file = media.mediaid
        WHERE NOW() <= ads.end AND ads.start IS NOT NULL
    """)

    return map(_from_row, all_ads)


def get_current_ads():
    now = _serializable_datetime(datetime.now())
    return [ad for ad in _get_all_ads() if ad["start"] <= now <= ad["end"]]


def get_display_ads(userid, count):
    current_ads = get_current_ads()
    return [Ad(**ad) for ad in random.sample(current_ads, min(count, len(current_ads)))]


def create_ad(form):
    if not form.target.startswith(("http://", "https://")):
        raise WeasylError("adTargetInvalid")

    if not form.image:
        raise WeasylError("adImageMissing")

    if len(form.image) > SIZE_LIMIT:
        raise WeasylError("adImageSizeInvalid")

    im = image.from_string(form.image)
    file_type = image.image_extension(im).lstrip(".")

    if file_type not in PERMITTED_TYPES:
        raise WeasylError("adImageTypeInvalid")

    ad_media = fetch_or_create_media_item(form.image, file_type=file_type, im=im)
    ad_media.dbsession.flush()

    ad_id = (
        engine.execute("""
            INSERT INTO ads (owner, link_target, file, start, "end")
            VALUES (%(owner)s, %(target)s, %(file)s, NOW(), %(end)s)
            RETURNING id
        """, owner=form.owner, target=form.target, file=ad_media.mediaid, end=form.end)
        .scalar())

    _get_all_ads.invalidate()
    return ad_id

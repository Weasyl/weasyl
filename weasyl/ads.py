import os
import random
import time

from datetime import datetime
from libweasyl.files import fanout
from libweasyl.models.media import fetch_or_create_media_item
from sanpera.geometry import Size
from weasyl import image
from weasyl.define import engine, region
from weasyl.error import WeasylError


class Ad(object):
    def __init__(self, id, link_target, start, end, image_path):
        self.id = id
        self.link_target = link_target
        self.start = start
        self.end = end
        self.image_path = image_path


IMAGE_DIMENSIONS = Size(300, 100)
PERMITTED_TYPES = {"jpg", "png", "gif"}
SIZE_LIMIT = 200 * 1024  # 200 KB


def _serializable_datetime(dt):
    if dt is None:
        return None

    return int(time.mktime(dt.timetuple()))


def _from_row(row):
    filename = "%s.%s" % (row.sha256, row.file_type)

    return {
        "id": row.id,
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
        SELECT ads.id, ads.link_target, ads.start, ads.end, media.sha256, media.file_type
        FROM ads
            INNER JOIN media ON ads.file = media.mediaid
        WHERE NOW() <= ads.end AND ads.start IS NOT NULL
    """)

    return map(_from_row, all_ads)


def _get_current_ads():
    now = _serializable_datetime(datetime.now())
    return [ad for ad in _get_all_ads() if ad["start"] <= now <= ad["end"]]


def get_current_ads():
    return [Ad(**ad) for ad in _get_current_ads()]


def get_display_ads(userid, count):
    current_ads = _get_current_ads()
    return [Ad(**ad) for ad in random.sample(current_ads, min(count, len(current_ads)))]


def create_ad(form):
    if not form.target.startswith(("http://", "https://")):
        raise WeasylError("adTargetInvalid")

    if not form.image:
        raise WeasylError("adImageMissing")

    if len(form.image) > SIZE_LIMIT:
        raise WeasylError("adImageSizeInvalid")

    im = image.from_string(form.image)
    file_type = image.image_file_type(im)

    if file_type not in PERMITTED_TYPES:
        raise WeasylError("adImageTypeInvalid")

    if im.size != IMAGE_DIMENSIONS:
        raise WeasylError("adImageDimensionsInvalid")

    ad_media = fetch_or_create_media_item(form.image, file_type=file_type, im=im)
    ad_media.dbsession.flush()

    ad_id = engine.scalar(
        """
        INSERT INTO ads (owner, link_target, file, start, "end")
        VALUES (%(owner)s, %(target)s, %(file)s, NOW(), %(end)s)
        RETURNING id
        """,
        owner=form.owner, target=form.target, file=ad_media.mediaid, end=form.end
    )

    _get_all_ads.invalidate()
    return ad_id


def expire(ad_id):
    engine.execute('UPDATE ads SET "end" = NOW() WHERE id = %(id)s', id=ad_id)
    _get_all_ads.invalidate()

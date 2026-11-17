import os

from weasyl import define as d
from weasyl import files
from weasyl import image
from weasyl import media
from weasyl import orm
from weasyl.error import WeasylError


def thumbnail_source(submitid):
    media_items = media.get_submission_media(submitid)
    source = None
    for link_type in ['thumbnail-source', 'cover']:
        if media_items.get(link_type):
            source = media_items[link_type][0]
            break
    if source is None:
        raise WeasylError('noImageSource')
    return source


def upload(filedata, submitid=None, charid=None):
    """
    Creates a preview-size copy of an uploaded image file for a new thumbnail
    selection file.
    """
    try:
        result = image.create_cover(filedata)
    except image.UnsupportedFormat as e:
        raise WeasylError("FileType") from e
    except Exception as e:
        raise WeasylError("imageProcessingFailed", level="info") from e

    if charid:
        filename = d.url_make(charid, "char/.thumb", root=True)
        with open(filename, "wb") as f:
            f.write(result.output)
    else:
        media_item = media.ensure_output_media(result)
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', media_item)


def create(x1, y1, x2, y2, submitid=None, charid=None,
           remove=True):
    x1, y1, x2, y2 = d.get_int(x1), d.get_int(y1), d.get_int(x2), d.get_int(y2)

    if charid:
        filename = d.url_make(charid, "char/.thumb", root=True)
        if not os.path.exists(filename):
            filename = d.url_make(charid, "char/cover", root=True)
            if not filename:
                return
            remove = False
    else:
        db = d.connect()
        source = thumbnail_source(submitid)
        filename = db.query(orm.MediaItem).get(source['mediaid']).full_file_path

    with open(filename, "rb") as f:
        image_bytes = f.read()

    try:
        result = image.create_thumbnail_crop(image_bytes, x1, y1, x2, y2)
    except Exception as e:
        raise WeasylError("imageProcessingFailed", level="info") from e

    if charid:
        d.engine.execute("""
            UPDATE character
            SET settings = REGEXP_REPLACE(settings, '-.', '') || '-' || %(image_setting)s
            WHERE charid = %(char)s
        """, image_setting=files.FILE_TYPE_FLAGS[result.output_file_type], char=charid)
        dest = os.path.join(d.get_character_directory(charid), '%i.thumb.%s' % (charid, result.output_file_type))

        with open(dest, "wb") as f:
            f.write(result.output)

        if remove:
            os.remove(filename)
    else:
        media_item = media.ensure_output_media(result)
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'thumbnail-custom', media_item)

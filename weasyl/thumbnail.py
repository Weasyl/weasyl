import os
from sanpera import geometry

from libweasyl import images

from weasyl import define as d
from weasyl import files
from weasyl import image
from weasyl import macro as m
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


def _upload_char(filedata, charid):
    """
    Creates a preview-size copy of an uploaded image file for a new thumbnail
    selection file.
    """
    filename = d.url_make(charid, "char/.thumb", root=True)

    files.write(filename, filedata)

    if image.check_type(filename):
        image.make_cover(filename)
    else:
        os.remove(filename)
        raise WeasylError("FileType")


def clear_thumbnail(userid, submitid):
    """
    Clears a submission's custom thumbnail.
    TODO: Ability to clear character thumbnails?
    TODO: This presently will clear both generated and custom thumbnails for
        non-visual submissions because we have a few multimedia/literary submissions
        whose thumbnails were generated from covers. If that ever ceases to be the
        case, revisit this logic.

    Args:
        userid: The userid requesting this operation. Used for permission checking.
        submitid: The submission to operate on.

    Returns:
        None
    """
    submission = orm.Submission.query.get(submitid)
    if not submission:
        raise WeasylError("Unexpected")
    if not submission.media.get('thumbnail-custom'):
        if submission.subtype < 2000 or not submission.media.get('thumbnail-generated'):
            raise WeasylError("noThumbnail")

    orm.SubmissionMediaLink.clear_link(submitid, 'thumbnail-custom')
    if submission.subtype >= 2000:
        orm.SubmissionMediaLink.clear_link(submitid, 'thumbnail-generated')


def upload(filedata, submitid=None, charid=None):
    if charid:
        return _upload_char(filedata, charid)

    media_item = media.make_cover_media_item(filedata, error_type='FileType')
    orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', media_item)


def _create_char(x1, y1, x2, y2, charid, remove=True):
    x1, y1, x2, y2 = d.get_int(x1), d.get_int(y1), d.get_int(x2), d.get_int(y2)
    filename = d.url_make(charid, "char/.thumb", root=True)
    if not m.os.path.exists(filename):
        filename = d.url_make(charid, "char/cover", root=True)
        if not filename:
            return
        remove = False

    im = image.read(filename)
    size = im.size.width, im.size.height

    d.engine.execute("""
        UPDATE character
        SET settings = REGEXP_REPLACE(settings, '-.', '') || '-' || %(image_setting)s
        WHERE charid = %(char)s
    """, image_setting=image.image_setting(im), char=charid)
    dest = os.path.join(d.get_character_directory(charid), '%i.thumb%s' % (charid, images.image_extension(im)))

    bounds = None
    if image.check_crop(size, x1, y1, x2, y2):
        bounds = geometry.Rectangle(x1, y1, x2, y2)
    thumb = images.make_thumbnail(im, bounds)
    thumb.write(dest, format=images.image_file_type(thumb))
    if remove:
        os.remove(filename)


def create(x1, y1, x2, y2, submitid=None, charid=None,
           remove=True):
    if charid:
        return _create_char(x1, y1, x2, y2, charid, remove)

    db = d.connect()
    x1, y1, x2, y2 = d.get_int(x1), d.get_int(y1), d.get_int(x2), d.get_int(y2)
    source = thumbnail_source(submitid)
    im = db.query(orm.MediaItem).get(source['mediaid']).as_image()
    size = im.size.width, im.size.height
    bounds = None
    if image.check_crop(size, x1, y1, x2, y2):
        bounds = geometry.Rectangle(x1, y1, x2, y2)
    thumb = images.make_thumbnail(im, bounds)
    file_type = images.image_file_type(im)
    media_item = orm.MediaItem.fetch_or_create(
        thumb.to_buffer(format=file_type), file_type=file_type, im=thumb)
    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'thumbnail-custom', media_item)

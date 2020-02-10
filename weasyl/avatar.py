from __future__ import absolute_import

from sanpera import geometry

from weasyl.error import WeasylError
from weasyl import define as d
from weasyl import image, media, orm


def avatar_source(userid):
    media_items = media.get_user_media(userid)
    if media_items.get('avatar-source'):
        return media_items['avatar-source'][0]
    else:
        raise WeasylError('noImageSource')


def upload(userid, filedata):
    """
    Creates a preview-size copy of an uploaded image file for a new avatar
    selection file.
    """
    if filedata:
        media_item = media.make_resized_media_item(filedata, (600, 500), 'FileType')
        orm.UserMediaLink.make_or_replace_link(userid, 'avatar-source', media_item)
    else:
        orm.UserMediaLink.clear_link(userid, 'avatar')

    return bool(filedata)


# TODO: Make this function respect new geometry.
def create(userid, x1, y1, x2, y2):
    x1, y1, x2, y2 = d.get_int(x1), d.get_int(y1), d.get_int(x2), d.get_int(y2)
    db = d.connect()
    im = db.query(orm.MediaItem).get(avatar_source(userid)['mediaid']).as_image()
    file_type = image.image_file_type(im)
    bounds = None
    size = im.size.width, im.size.height
    if image.check_crop(size, x1, y1, x2, y2):
        bounds = geometry.Rectangle(x1, y1, x2, y2)
    thumb = image.shrinkcrop(im, geometry.Size(100, 100), bounds)
    media_item = orm.MediaItem.fetch_or_create(
        thumb.to_buffer(format=file_type), file_type=file_type, im=thumb)
    orm.UserMediaLink.make_or_replace_link(userid, 'avatar', media_item)
    orm.UserMediaLink.clear_link(userid, 'avatar-source')

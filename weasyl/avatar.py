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
        try:
            result = image.create_avatar_source(filedata)
        except image.UnsupportedFormat as e:
            raise WeasylError("FileType") from e
        except Exception as e:
            raise WeasylError("imageProcessingFailed", level="info") from e
        media_item = media.ensure_output_media(result)
        orm.UserMediaLink.make_or_replace_link(userid, 'avatar-source', media_item)
    else:
        orm.UserMediaLink.clear_link(userid, 'avatar')

    return bool(filedata)


def create(userid, x1, y1, x2, y2):
    x1, y1, x2, y2 = d.get_int(x1), d.get_int(y1), d.get_int(x2), d.get_int(y2)
    db = d.connect()
    with open(db.query(orm.MediaItem).get(avatar_source(userid)['mediaid']).full_file_path, "rb") as f:
        image_bytes = f.read()
    result = image.create_avatar(image_bytes, x1, y1, x2, y2)
    media_item = media.ensure_output_media(result)
    orm.UserMediaLink.make_or_replace_link(userid, 'avatar', media_item)
    orm.UserMediaLink.clear_link(userid, 'avatar-source')

from weasyl import image, media, orm
from weasyl.error import WeasylError


def upload(userid, filedata):
    """
    Creates a preview-size copy of an uploaded image for a new banner
    selection file.
    """
    if not filedata:
        orm.UserMediaLink.clear_link(userid, 'banner')
        return

    try:
        result = image.create_banner(filedata)
    except image.UnsupportedFormat as e:
        raise WeasylError("FileType") from e
    except Exception as e:
        raise WeasylError("imageProcessingFailed", level="info") from e

    media_item = media.ensure_output_media(result)
    orm.UserMediaLink.make_or_replace_link(userid, 'banner', media_item)

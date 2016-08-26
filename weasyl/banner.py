from libweasyl import media
from libweasyl import ratings
from libweasyl.models.media import UserMediaLink


def upload(userid, filedata):
    """
    Creates a preview-size copy of an uploaded image for a new banner
    selection file.
    """
    if not filedata:
        UserMediaLink.clear_link(userid, 'banner')
        return

    media_item = media.make_resized_media_item(filedata, (1650, 250))
    UserMediaLink.make_or_replace_link(
        userid, 'banner', media_item, rating=ratings.GENERAL.code)

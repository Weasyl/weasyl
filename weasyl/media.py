from libweasyl import images
from libweasyl import media as libweasylmedia
from libweasyl.text import slug_for

from weasyl.error import WeasylError
from weasyl import define, image, orm


def make_resized_media_item(filedata, size, error_type='FileType'):
    if not filedata:
        return None

    im = image.from_string(filedata)
    file_type = images.image_file_type(im)
    if file_type not in ["jpg", "png", "gif"]:
        raise WeasylError(error_type)
    resized = images.resize_image(im, *size)
    if resized is not im:
        filedata = resized.to_buffer(format=file_type)
    return orm.MediaItem.fetch_or_create(filedata, file_type=file_type, im=resized)


def make_cover_media_item(coverfile, error_type='coverType'):
    return make_resized_media_item(coverfile, image.COVER_SIZE, error_type)


def get_multi_submission_media(*submitids):
    ret = libweasylmedia.get_multi_submission_media(*submitids)
    for d in ret:
        d.setdefault('thumbnail-generated', define.DEFAULT_SUBMISSION_THUMBNAIL)
    return ret


def get_multi_user_media(*userids):
    ret = libweasylmedia.get_multi_user_media(*userids)
    for d in ret:
        d.setdefault('avatar', define.DEFAULT_AVATAR)
    return ret


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, media_key, multi_get):
    def populator(dicts):
        if not dicts:
            return
        keys_to_fetch = [d[identity] for d in dicts]
        for d, value in zip(dicts, multi_get(*keys_to_fetch)):
            d[media_key] = value
    return populator


populate_with_submission_media = build_populator('submitid', 'sub_media', get_multi_submission_media)
populate_with_user_media = build_populator('userid', 'user_media', get_multi_user_media)


def format_media_link(media, link):
    if link.link_type == 'submission':
        login_name = link.submission.owner.login_name
        formatted_url = '/~%s/submissions/%s/%s/%s-%s.%s' % (
            login_name, link.submitid, media.sha256, login_name,
            slug_for(link.submission.title), media.file_type)
        return define.cdnify_url(formatted_url)
    elif link.link_type in ['cover', 'thumbnail-custom',
                            'thumbnail-generated', 'thumbnail-generated-webp',
                            'avatar', 'banner']:
        return define.cdnify_url(media.display_url)
    else:
        return None


def strip_non_thumbnail_media(submissions):
    """
    Remove all media from a submission dict except what’s necessary to render its thumbnail.

    Useful for reducing the size of JSON in cache.
    """
    for sub in submissions:
        sub_media = sub["sub_media"]
        sub_media.pop("thumbnail-source", None)
        sub_media.pop("cover", None)
        sub_media.pop("submission", None)

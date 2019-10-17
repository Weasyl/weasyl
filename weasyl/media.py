

from libweasyl import media as libweasylmedia
from libweasyl.text import slug_for

from weasyl.error import WeasylError
from weasyl import macro as m
from weasyl import define, image, orm


def make_resized_media_item(filedata, size, error_type='FileType'):
    if not filedata:
        return None

    im = image.from_string(filedata)
    file_type = image.image_file_type(im)
    if file_type not in ["jpg", "png", "gif"]:
        raise WeasylError(error_type)
    resized = image.resize_image(im, *size)
    if resized is not im:
        filedata = resized.to_buffer(format=file_type)
    return orm.fetch_or_create_media_item(filedata, file_type=file_type, im=resized)


def make_cover_media_item(coverfile, error_type='coverType'):
    return make_resized_media_item(coverfile, image.COVER_SIZE, error_type)


def get_multi_submission_media(*submitids):
    ret = libweasylmedia.get_multi_submission_media(*submitids)
    for d in ret:
        d.setdefault('thumbnail-generated', m.MACRO_DEFAULT_SUBMISSION_THUMBNAIL)
    return ret


def get_multi_user_media(*userids):
    ret = libweasylmedia.get_multi_user_media(*userids)
    for d in ret:
        d.setdefault('avatar', m.MACRO_DEFAULT_AVATAR)
    return ret


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, media_key, multi_get):
    def populator(dicts, strict=True):
        to_fetch = []
        for e, d in enumerate(dicts):
            if identity not in d:
                if strict:
                    raise KeyError(identity, d)
                else:
                    continue
            to_fetch.append((d[identity], e))
        if not to_fetch:
            return dicts
        keys_to_fetch, indices = list(zip(*to_fetch))
        for index, value in zip(indices, multi_get(*keys_to_fetch)):
            dicts[index][media_key] = value
        return dicts
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
    elif link.link_type in ['cover', 'thumbnail-custom', 'thumbnail-legacy',
                            'thumbnail-generated', 'thumbnail-generated-webp',
                            'avatar', 'banner']:
        return define.cdnify_url(media.display_url)
    else:
        return None

from __future__ import absolute_import

import base64
import struct

from libweasyl import media as libweasylmedia
from libweasyl.text import slug_for

from weasyl.error import WeasylError
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
    elif link.link_type in ['cover', 'thumbnail-custom', 'thumbnail-legacy',
                            'thumbnail-generated', 'thumbnail-generated-webp',
                            'avatar', 'banner']:
        return define.cdnify_url(media.display_url)
    else:
        return None


_IMAGE_FILE_TYPES = ('png', 'jpg', 'gif', 'webp')
_CDN2_PREFIX = define.config_read_setting('prefix', section='cdn2')


def _deserialize_image_representation(serialized):
    content_type = ord(serialized[0])
    file_key = serialized[1:17]
    width, height = struct.unpack_from('>HH', serialized, 17)

    file_type = _IMAGE_FILE_TYPES[content_type - 1]
    filename = base64.urlsafe_b64encode(file_key).rstrip('=') + '.' + file_type

    return {
        'file_type': file_type,
        'display_url': _CDN2_PREFIX + filename,
        'attributes': {
            'width': str(width),
            'height': str(height),
        },
    }


# see https://github.com/Weasyl/mediacopy
def deserialize_image_representations(serialized):
    # a bit is set in the first byte for every optional representation
    included_mask = ord(serialized[0])
    offset = 1

    # each image representation is 21 bytes
    original = _deserialize_image_representation(serialized[offset:offset+21])
    offset += 21

    if included_mask & 1:
        cover = _deserialize_image_representation(serialized[offset:offset+21])
        offset += 21
    else:
        cover = original

    if included_mask & 2:
        thumbnail_generated = _deserialize_image_representation(serialized[offset:offset+21])
        offset += 21
    else:
        thumbnail_generated = cover

    if included_mask & 4:
        thumbnail_custom = _deserialize_image_representation(serialized[offset:offset+21])
        offset += 21
    else:
        thumbnail_custom = None

    if included_mask & 32:
        thumbnail_generated_webp = _deserialize_image_representation(serialized[offset:offset+21])
        offset += 21
    else:
        thumbnail_generated_webp = None

    if included_mask & ~(1 | 2 | 4 | 32):
        raise ValueError('Unsupported representations in mask: 0b{:b}'.format(included_mask))

    media = {
        'submission': [original],
        'cover': [cover],
        'thumbnail-generated': [thumbnail_generated],
    }

    if thumbnail_custom is not None:
        media['thumbnail-custom'] = [thumbnail_custom]

    if thumbnail_generated_webp is not None:
        media['thumbnail-generated-webp'] = [thumbnail_generated_webp]

    return media


def populate_with_remaining_submission_media(dicts):
    remaining = []

    for d in dicts:
        image_representations = d.pop('image_representations', None)

        if image_representations is None or _CDN2_PREFIX is None:
            remaining.append(d)
        else:
            d['sub_media'] = deserialize_image_representations(image_representations)

    populate_with_submission_media(remaining)

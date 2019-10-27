from libweasyl.cache import region
from libweasyl.constants import Category
from libweasyl.models.media import SubmissionMediaLink, UserMediaLink, fetch_or_create_media_item
from libweasyl import files, images


@SubmissionMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_submission_media(*submitids):
    return SubmissionMediaLink.bucket_links(submitids)


@UserMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_user_media(*userids):
    return UserMediaLink.bucket_links(userids)


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, multi_get):
    def populator(objects):
        # using vars like this is nasty, but is required in this case
        # because hasattr will try to actually fetch the attribute,
        # and fetching the attribute will fetch the media.
        needy_objects = list({o for o in objects if 'media' not in vars(o)})
        if not needy_objects:
            return
        keys_to_fetch = [getattr(o, identity) for o in needy_objects]
        for o, value in zip(needy_objects, multi_get(*keys_to_fetch)):
            o.media = value
    return populator


populate_with_submission_media = build_populator('submitid', get_multi_submission_media)
populate_with_user_media = build_populator('userid', get_multi_user_media)


def make_resized_media_item(data, size):
    """
    Resizes raw image data and makes a media item for it. This method only
    shrinks images; it will not zoom them if size describes larger dimensions.

    Parameters:
        data: The raw data as :term:`bytes`.
        size (tuple): A ``width, height`` tuple representing target size.

    Returns:
        A media item.
    """
    im, im_format = files.file_type_for_category(data, Category.visual)
    resized = images.resize_image(im, *size)
    if resized is not im:
        data = resized.to_buffer(format=im_format)
    return fetch_or_create_media_item(data, file_type=im_format, im=resized)


def make_cover_media_item(coverfile):
    return make_resized_media_item(coverfile, images.COVER_SIZE)


__all__ = [
    'fetch_or_create_media_item', 'populate_with_submission_media', 'populate_with_user_media',
    'make_resized_media_item', 'make_cover_media_item',
]

from libweasyl.cache import region
from libweasyl.models.media import MediaItem, SubmissionMediaLink, UserMediaLink


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


__all__ = [
    'MediaItem', 'get_submission_media', 'get_user_media',
]

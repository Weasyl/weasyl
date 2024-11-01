from libweasyl.cache import region
from libweasyl.models.media import MediaItem, SerializedMediaItem, SubmissionMediaLink, UserMediaLink


@SubmissionMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_submission_media(*submitids: int) -> list[dict[str, list[SerializedMediaItem]]]:
    return SubmissionMediaLink.bucket_links(submitids)


@UserMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_user_media(*userids: int) -> list[dict[str, list[SerializedMediaItem]]]:
    return UserMediaLink.bucket_links(userids)


def get_submission_media(submitid: int) -> dict[str, list[SerializedMediaItem]]:
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid: int) -> dict[str, list[SerializedMediaItem]]:
    return get_multi_user_media(userid)[0]


__all__ = [
    'MediaItem', 'get_submission_media', 'get_user_media', 'get_multi_user_media',
]

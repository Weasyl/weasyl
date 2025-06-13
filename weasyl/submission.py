import os
import re
from io import BytesIO
from urllib.parse import urlparse

import arrow
import sqlalchemy as sa
from sqlalchemy import bindparam

from libweasyl.cache import region
from libweasyl.models.media import MediaItem
from libweasyl.models.tables import google_doc_embeds
from libweasyl import (
    images,
    images_new,
    staff,
    text,
)

from weasyl import api
from weasyl import blocktag
from weasyl import collection
from weasyl import comment
from weasyl import define as d
from weasyl import embed
from weasyl import favorite
from weasyl import files
from weasyl import folder
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import image
from weasyl import macro as m
from weasyl import media
from weasyl import orm
from weasyl import profile
from weasyl import report
from weasyl import searchtag
from weasyl import welcome
from weasyl.error import WeasylError


COUNT_LIMIT = 250

_MEGABYTE = 1048576

_LIMITS = {
    ".jpg": 50 * _MEGABYTE,
    ".png": 50 * _MEGABYTE,
    ".gif": 50 * _MEGABYTE,
    ".txt": 2 * _MEGABYTE,
    ".pdf": 10 * _MEGABYTE,
    ".htm": 10 * _MEGABYTE,
    ".mp3": 15 * _MEGABYTE,
    ".swf": 50 * _MEGABYTE,
}


def _limit(size, extension):
    """
    Return True if the file size exceeds the limit designated to the specified
    file type, else False.
    """
    limit = _LIMITS[extension]
    return size > limit


def _create_notifications(userid, submitid, rating, *, friends_only):
    """
    Creates notifications to watchers.
    """
    welcome.submission_insert(userid, submitid, rating=rating.code, friends_only=friends_only)


def check_for_duplicate_media(userid, mediaid):
    db = d.connect()
    q = (
        db.query(orm.Submission)
        .filter_by(userid=userid, hidden=False)
        .join(orm.SubmissionMediaLink)
        .filter_by(mediaid=mediaid, link_type='submission'))
    if q.first():
        raise WeasylError('duplicateSubmission')


def _create_submission(expected_type):
    valid_types = {id for (id, name) in m.MACRO_SUBCAT_LIST if id // 1000 == expected_type}

    def wrapper(create_specific):
        def create_generic(userid, submission, **kwargs):
            tags = kwargs['tags']

            if submission.subtype not in valid_types:
                submission.subtype = expected_type * 1000 + 999

            if not submission.title:
                raise WeasylError("titleInvalid")
            elif not submission.rating:
                raise WeasylError("ratingInvalid")
            elif len(tags) < 2:
                raise WeasylError("notEnoughTags")
            elif not folder.check(userid, submission.folderid):
                raise WeasylError("Unexpected")

            profile.check_user_rating_allowed(userid, submission.rating)
            if submission.rating.minimum_age:
                profile.assert_adult(userid)

            newid = create_specific(
                userid=userid,
                submission=submission,
                **kwargs)
            if newid:
                p = d.meta.tables['profile']
                d.connect().execute(p.update().where(p.c.userid == userid).values(latest_submission_time=arrow.utcnow()))
                d.cached_posts_count.invalidate(userid)
            return newid

        return create_generic

    return wrapper


_ALLOWED_CROSSPOST_HOSTS = frozenset([
    # DeviantArt
    "wixmp.com",

    # Fur Affinity
    "furaffinity.net",
    "facdn.net",

    # Imgur
    "imgur.com",

    # Inkbunny
    "ib.metapix.net",

    # SoFurry
    "sofurryfiles.com",
])

_ALLOWED_CROSSPOST_HOST = re.compile(
    r"(?:\A|\.)"
    + "(?:" + "|".join(map(re.escape, _ALLOWED_CROSSPOST_HOSTS)) + ")"
    + r"\Z"
)


def _http_get_if_crosspostable(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or _ALLOWED_CROSSPOST_HOST.search(parsed.netloc) is None:
        raise WeasylError("crosspostInvalid")

    return d.http_get(url, timeout=5)


@_create_submission(expected_type=1)
def create_visual(userid, submission,
                  friends_only, tags, imageURL, thumbfile,
                  submitfile, critique, create_notifications):
    if imageURL:
        resp = _http_get_if_crosspostable(imageURL)
        submitfile = resp.content

    # Determine filesizes
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    if not submitsize:
        raise WeasylError("submitSizeZero")
    elif thumbsize > 10 * _MEGABYTE:
        raise WeasylError("thumbSizeExceedsLimit")

    im = image.from_string(submitfile)
    submitextension = images.image_extension(im)
    if submitextension not in [".jpg", ".png", ".gif"]:
        raise WeasylError("submitType")
    if _limit(submitsize, submitextension):
        raise WeasylError("submitSizeExceedsLimit")

    submit_file_type = submitextension.lstrip('.')
    submit_media_item = orm.MediaItem.fetch_or_create(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    cover_media_item = submit_media_item.ensure_cover_image(im)

    # Thumbnail stuff.
    # Always create a 'generated' thumbnail from the source image.
    with BytesIO(submitfile) as buf:
        thumbnail_formats = images_new.get_thumbnail(buf)

    thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.compatible
    thumb_generated_media_item = orm.MediaItem.fetch_or_create(
        thumb_generated,
        file_type=thumb_generated_file_type,
        attributes=thumb_generated_attributes,
    )

    if thumbnail_formats.webp is None:
        thumb_generated_media_item_webp = None
    else:
        thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.webp
        thumb_generated_media_item_webp = orm.MediaItem.fetch_or_create(
            thumb_generated,
            file_type=thumb_generated_file_type,
            attributes=thumb_generated_attributes,
        )

    # If requested, also create a 'custom' thumbnail.
    thumb_media_item = media.make_cover_media_item(thumbfile)
    if thumb_media_item:
        thumb_custom = images.make_thumbnail(image.from_string(thumbfile))
        thumb_custom_media_item = orm.MediaItem.fetch_or_create(
            thumb_custom.to_buffer(format=submit_file_type), file_type=submit_file_type,
            im=thumb_custom)

    # TODO(kailys): maintain ORM object
    db = d.connect()
    now = arrow.get()
    q = (
        d.meta.tables['submission'].insert().values([{
            "folderid": submission.folderid,
            "userid": userid,
            "unixtime": now,
            "title": submission.title,
            "content": submission.content,
            "subtype": submission.subtype,
            "rating": submission.rating.code,
            "friends_only": friends_only,
            "critique": critique,
            "favorites": 0,
            "submitter_ip_address": submission.submitter_ip_address,
            "submitter_user_agent_id": submission.submitter_user_agent_id,
        }]).returning(d.meta.tables['submission'].c.submitid))
    submitid = db.scalar(q)

    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'submission', submit_media_item)
    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'cover', cover_media_item)

    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'thumbnail-generated', thumb_generated_media_item)

    if thumb_generated_media_item_webp is not None:
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'thumbnail-generated-webp', thumb_generated_media_item_webp)

    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'thumbnail-custom', thumb_custom_media_item)

    # Assign search tags
    searchtag.associate(
        userid=userid,
        target=searchtag.SubmissionTarget(submitid),
        tag_names=tags,
    )

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, friends_only=friends_only)

    d.metric('increment', 'submissions')
    d.metric('increment', 'visualsubmissions')

    return submitid


_GOOGLE_DOCS_EMBED = re.compile(
    r"\bdocs\.google\.com/document/d/((?:e/)?[0-9a-z_\-]+)/pub\b",
    re.ASCII | re.IGNORECASE,
)


def _normalize_google_docs_embed(embedlink):
    match = _GOOGLE_DOCS_EMBED.search(embedlink.strip())

    if match is None:
        raise WeasylError('googleDocsEmbedLinkInvalid', level='info')

    return f"https://docs.google.com/document/d/{match.group(1)}/pub?embedded=true"


@_create_submission(expected_type=2)
def create_literary(userid, submission, embedlink=None, friends_only=False, tags=None,
                    coverfile=None, thumbfile=None, submitfile=None, critique=False,
                    create_notifications=True):
    if embedlink:
        embedlink = _normalize_google_docs_embed(embedlink)

    # Determine filesizes
    coversize = len(coverfile)
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    if not submitsize and not embedlink:
        raise WeasylError("submitSizeZero")
    elif coversize > 10 * _MEGABYTE:
        raise WeasylError("coverSizeExceedsLimit")
    elif thumbsize > 10 * _MEGABYTE:
        raise WeasylError("thumbSizeExceedsLimit")

    if submitsize:
        submitextension = files.get_extension_for_category(submitfile, m.TEXT_SUBMISSION_CATEGORY)
        if submitextension is None:
            raise WeasylError("submitType")
        if _limit(submitsize, submitextension):
            raise WeasylError("submitSizeExceedsLimit")
        submit_media_item = orm.MediaItem.fetch_or_create(
            submitfile, file_type=submitextension.lstrip('.'))
        check_for_duplicate_media(userid, submit_media_item.mediaid)
    else:
        submit_media_item = None

    thumb_media_item = media.make_cover_media_item(thumbfile)
    cover_media_item = media.make_cover_media_item(coverfile)
    if cover_media_item and not thumb_media_item:
        thumb_media_item = cover_media_item

    # Create submission
    # TODO(kailys): use ORM object
    db = d.connect()
    now = arrow.get()
    q = (
        d.meta.tables['submission'].insert().values([{
            "folderid": submission.folderid,
            "userid": userid,
            "unixtime": now,
            "title": submission.title,
            "content": submission.content,
            "subtype": submission.subtype,
            "rating": submission.rating.code,
            "friends_only": friends_only,
            "critique": critique,
            "embed_type": 'google-drive' if embedlink else None,
            "favorites": 0,
            "submitter_ip_address": submission.submitter_ip_address,
            "submitter_user_agent_id": submission.submitter_user_agent_id,
        }])
        .returning(d.meta.tables['submission'].c.submitid))
    submitid = db.scalar(q)
    if embedlink:
        q = (d.meta.tables['google_doc_embeds'].insert()
             .values(submitid=submitid, embed_url=embedlink))
        db.execute(q)

    # Assign search tags
    searchtag.associate(
        userid=userid,
        target=searchtag.SubmissionTarget(submitid),
        tag_names=tags,
    )

    if submit_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'submission', submit_media_item)
    if cover_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)
    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, friends_only=friends_only)

    d.metric('increment', 'submissions')
    d.metric('increment', 'literarysubmissions')

    return submitid, bool(thumb_media_item)


@_create_submission(expected_type=3)
def create_multimedia(userid, submission, embedlink=None, friends_only=None,
                      tags=None, coverfile=None, thumbfile=None, submitfile=None,
                      critique=False, create_notifications=True, auto_thumb=False):
    embedlink = embedlink.strip()

    # Determine filesizes
    coversize = len(coverfile)
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    if not submitsize and not embedlink:
        raise WeasylError("submitSizeZero")
    elif embedlink and not embed.check_valid(embedlink):
        raise WeasylError("embedlinkInvalid")
    elif coversize > 10 * _MEGABYTE:
        raise WeasylError("coverSizeExceedsLimit")
    elif thumbsize > 10 * _MEGABYTE:
        raise WeasylError("thumbSizeExceedsLimit")

    if submitsize:
        submitextension = files.get_extension_for_category(submitfile, m.MULTIMEDIA_SUBMISSION_CATEGORY)
        if submitextension is None:
            raise WeasylError("submitType")
        elif submitextension not in [".mp3", ".swf"] and not embedlink:
            raise WeasylError("submitType")
        elif _limit(submitsize, submitextension):
            raise WeasylError("submitSizeExceedsLimit")
        submit_media_item = orm.MediaItem.fetch_or_create(
            submitfile, file_type=submitextension.lstrip('.'))
        check_for_duplicate_media(userid, submit_media_item.mediaid)
    else:
        submit_media_item = None

    thumb_media_item = media.make_cover_media_item(thumbfile)
    cover_media_item = media.make_cover_media_item(coverfile)
    if cover_media_item and not thumb_media_item:
        thumb_media_item = cover_media_item

    tempthumb_media_item = None
    im = None
    if auto_thumb:
        if thumbsize == 0 and coversize == 0:
            # Fetch default thumbnail from source if available
            thumb_url = embed.thumbnail(embedlink)
            if thumb_url:
                resp = d.http_get(thumb_url, timeout=5)
                im = image.from_string(resp.content)
    if not im and (thumbsize or coversize):
        im = image.from_string(thumbfile or coverfile)
    if im:
        tempthumb = images.make_thumbnail(im)
        tempthumb_type = images.image_file_type(tempthumb)
        tempthumb_media_item = orm.MediaItem.fetch_or_create(
            tempthumb.to_buffer(format=tempthumb_type),
            file_type=tempthumb_type,
            im=tempthumb)

    # Inject embedlink
    if embedlink:
        submission.content = "".join([embedlink, "\n", submission.content])

    # Create submission
    db = d.connect()
    now = arrow.get()
    q = (
        d.meta.tables['submission'].insert().values([{
            "folderid": submission.folderid,
            "userid": userid,
            "unixtime": now,
            "title": submission.title,
            "content": submission.content,
            "subtype": submission.subtype,
            "rating": submission.rating,
            "friends_only": friends_only,
            "critique": critique,
            "embed_type": 'other' if embedlink else None,
            "favorites": 0,
            "submitter_ip_address": submission.submitter_ip_address,
            "submitter_user_agent_id": submission.submitter_user_agent_id,
        }])
        .returning(d.meta.tables['submission'].c.submitid))
    submitid = db.scalar(q)

    # Assign search tags
    searchtag.associate(
        userid=userid,
        target=searchtag.SubmissionTarget(submitid),
        tag_names=tags,
    )

    if submit_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'submission', submit_media_item)
    if cover_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)
    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)
    if tempthumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-custom',
                                                     tempthumb_media_item)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, friends_only=friends_only)

    d.metric('increment', 'submissions')
    d.metric('increment', 'multimediasubmissions')

    return submitid, bool(thumb_media_item)


def reupload(userid, submitid, submitfile):
    submitsize = len(submitfile)

    # Select submission data
    query = d.engine.execute(
        "SELECT userid, subtype, embed_type FROM submission WHERE submitid = %(id)s AND NOT hidden",
        id=submitid,
    ).first()

    if not query:
        raise WeasylError("Unexpected")
    elif userid != query[0]:
        raise WeasylError("Unexpected")
    elif query[2] is not None:
        raise WeasylError("Unexpected")

    subcat = query[1] // 1000 * 1000
    if subcat not in m.ALL_SUBMISSION_CATEGORIES:
        raise WeasylError("Unexpected")

    # Check invalid file data
    if not submitsize:
        raise WeasylError("submitSizeZero")

    # Write temporary submission file
    submitextension = files.get_extension_for_category(submitfile, subcat)
    if submitextension is None:
        raise WeasylError("submitType")
    elif subcat == m.ART_SUBMISSION_CATEGORY and submitextension not in [".jpg", ".png", ".gif"]:
        raise WeasylError("submitType")
    elif subcat == m.MULTIMEDIA_SUBMISSION_CATEGORY and submitextension not in [".mp3", ".swf"]:
        raise WeasylError("submitType")
    elif _limit(submitsize, submitextension):
        raise WeasylError("submitSizeExceedsLimit")

    submit_file_type = submitextension.lstrip('.')
    im = None
    if submit_file_type in {'jpg', 'png', 'gif'}:
        im = image.from_string(submitfile)
    submit_media_item = orm.MediaItem.fetch_or_create(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    orm.SubmissionMediaLink.make_or_replace_link(submitid, 'submission', submit_media_item)

    if subcat == m.ART_SUBMISSION_CATEGORY:
        cover_media_item = submit_media_item.ensure_cover_image(im)
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)

        # Always create a 'generated' thumbnail from the source image.
        with BytesIO(submitfile) as buf:
            thumbnail_formats = images_new.get_thumbnail(buf)

        thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.compatible
        thumb_generated_media_item = orm.MediaItem.fetch_or_create(
            thumb_generated,
            file_type=thumb_generated_file_type,
            attributes=thumb_generated_attributes,
        )

        if thumbnail_formats.webp is None:
            thumb_generated_media_item_webp = None
        else:
            thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.webp
            thumb_generated_media_item_webp = orm.MediaItem.fetch_or_create(
                thumb_generated,
                file_type=thumb_generated_file_type,
                attributes=thumb_generated_attributes,
            )

        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-generated', thumb_generated_media_item)

        if thumbnail_formats.webp is not None:
            orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-generated-webp', thumb_generated_media_item_webp)


_GOOGLE_DOCS_EMBED_URL_QUERY = (
    sa.select([google_doc_embeds.c.embed_url])
    .where(google_doc_embeds.c.submitid == bindparam('submitid'))
)


def get_google_docs_embed_url(submitid):
    embed_url = d.engine.scalar(
        _GOOGLE_DOCS_EMBED_URL_QUERY,
        {"submitid": submitid},
    )

    if embed_url is None:
        raise WeasylError("Unexpected")  # pragma: no cover

    return embed_url


def select_view(userid, submitid, rating, ignore=True, anyway=None):
    # TODO(hyena): This `query[n]` stuff is monstrous. Use named fields.
    # Also some of these don't appear to be used? e.g. pr.config
    query = d.engine.execute("""
        SELECT
            su.userid, pr.username, su.folderid, su.unixtime, su.title, su.content, su.subtype, su.rating,
            su.hidden, su.friends_only, su.critique, su.embed_type,
            su.page_views, fd.title, su.favorites
        FROM submission su
            INNER JOIN profile pr USING (userid)
            LEFT JOIN folder fd USING (folderid)
        WHERE su.submitid = %(id)s
    """, id=submitid).first()

    # Sanity check
    if query and userid in staff.MODS and anyway == "true":
        pass
    elif not query or query[8]:
        raise WeasylError("submissionRecordMissing")
    elif query[7] > rating and ((userid != query[0] and userid not in staff.MODS) or d.is_sfw_mode()):
        raise WeasylError("RatingExceeded")
    elif query[9] and not frienduser.check(userid, query[0]):
        raise WeasylError("FriendsOnly")
    elif ignore and ignoreuser.check(userid, query[0]):
        raise WeasylError("UserIgnored")
    elif ignore and blocktag.check(userid, submitid=submitid):
        raise WeasylError("TagBlocked")

    # Get submission filename
    submitfile = media.get_submission_media(submitid).get('submission', [None])[0]

    # Get submission text
    if submitfile and submitfile['file_type'] in ['txt', 'htm']:
        submittext = files.read(os.path.join(MediaItem._base_file_path, submitfile['file_url'][1:]))
    else:
        submittext = None

    embedlink = d.text_first_line(query[5]) if query[11] == 'other' else None

    google_doc_embed = None
    if query[11] == 'google-drive':
        google_doc_embed = get_google_docs_embed_url(submitid)

    grouped_tags = searchtag.select_grouped(userid, searchtag.SubmissionTarget(submitid))
    settings = d.get_profile_settings(query[0])

    sub_media = media.get_submission_media(submitid)

    return {
        "submitid": submitid,
        "userid": query[0],
        "username": query[1],
        "folderid": query[2],
        "unixtime": query[3],
        "title": query[4],
        "content": (d.text_first_line(query[5], strip=True) if 'other' == query[11] else query[5]),
        "subtype": query[6],
        "rating": query[7],
        "hidden": query[8],
        "friends_only": query[9],
        "critique": query[10],
        "embed_type": query[11],
        "page_views": (
            query[12] + 1 if d.common_view_content(userid, 0 if anyway == "true" else submitid, "submit") else query[12]),
        "fave_count": query[14],


        "mine": userid == query[0],
        "reported": report.check(submitid=submitid),
        "favorited": favorite.check(userid, submitid=submitid),
        "collected": collection.owns(userid, submitid),
        "no_request": not settings.allow_collection_requests,

        "text": submittext,
        "sub_media": sub_media,
        "user_media": media.get_user_media(query[0]),
        "submit": submitfile,
        "embedlink": embedlink,
        "embed": embed.html(embedlink) if embedlink is not None else None,
        "google_doc_embed": google_doc_embed,


        "tags": grouped_tags,
        "folder_more": select_near(userid, rating, 1, query[0], query[2], submitid),
        "folder_title": query[13] if query[13] else "Root",


        "comments": comment.select(userid, submitid=submitid),
    }


def select_view_api(userid, submitid, anyway=False, increment_views=False):
    rating = d.get_rating(userid)
    db = d.connect()
    sub = db.query(orm.Submission).get(submitid)
    if sub is None or sub.hidden:
        raise WeasylError("submissionRecordMissing")
    sub_rating = sub.rating.code
    if sub.friends_only and not frienduser.check(userid, sub.userid):
        raise WeasylError("submissionRecordMissing")
    elif sub_rating > rating and userid != sub.userid:
        raise WeasylError("RatingExceeded")
    elif not anyway and ignoreuser.check(userid, sub.userid):
        raise WeasylError("UserIgnored")
    elif not anyway and blocktag.check(userid, submitid=submitid):
        raise WeasylError("TagBlocked")

    description = sub.content
    embedlink = None
    if sub.embed_type == 'other':
        embedlink, _, description = description.partition('\n')
    elif sub.embed_type == 'google-drive':
        embedlink = get_google_docs_embed_url(submitid)

    views = sub.page_views
    if increment_views and d.common_view_content(userid, submitid, 'submit'):
        views += 1

    return {
        'submitid': submitid,
        'title': sub.title,
        'owner': sub.owner.profile.username,
        'owner_login': sub.owner.login_name,
        'owner_media': api.tidy_all_media(media.get_user_media(sub.userid)),
        'media': api.tidy_all_media(media.get_submission_media(submitid)),
        'description': text.markdown(description),
        'embedlink': embedlink,
        'folderid': sub.folderid,
        'folder_name': sub.folder.title if sub.folderid else None,
        'posted_at': d.iso8601(sub.unixtime),
        'tags': searchtag.select(submitid=submitid),
        'link': d.absolutify_url("/submission/%d/%s" % (submitid, text.slug_for(sub.title))),

        'type': 'submission',
        'subtype': m.CATEGORY_PARSABLE_MAP[sub.subtype // 1000 * 1000],
        'rating': sub.rating.name,

        'views': views,
        'favorites': sub.favorites,
        'comments': comment.count(submitid),
        'favorited': favorite.check(userid, submitid=submitid),
        'friends_only': sub.friends_only,
    }


def _select_query(
    *,
    userid,
    rating,
    otherid,
    folderid,
    backid,
    nextid,
    subcat,
    profile_page_filter,
    index_page_filter,
    featured_filter,
    critique_only
):
    statement = [
        "FROM submission su "
        "INNER JOIN profile pr ON su.userid = pr.userid "
        "LEFT JOIN folder f USING (folderid) "
        "WHERE NOT hidden"]
    if profile_page_filter:
        statement.append(" AND COALESCE(f.settings !~ 'u', true)")
    if index_page_filter:
        statement.append(" AND COALESCE(f.settings !~ 'm', true)")
    if featured_filter:
        statement.append(" AND COALESCE(f.settings ~ 'f', false)")

    # Logged in users will see their own submissions regardless of rating
    # EXCEPT if they are in SFW mode
    if userid and not d.is_sfw_mode():
        statement.append(" AND (su.rating <= %i OR su.userid = %i)" % (rating, userid))
    else:
        statement.append(" AND su.rating <= %i" % (rating,))

    if otherid:
        statement.append(" AND su.userid = %i" % (otherid,))

    if folderid:
        statement.append(" AND su.folderid = %i" % (folderid,))

    if subcat:
        statement.append(" AND su.subtype >= %i AND su.subtype < %i" % (subcat, subcat + 1000))

    if critique_only:
        statement.append(" AND su.critique")

    if backid:
        statement.append(" AND su.submitid > %i" % (backid,))
    elif nextid:
        statement.append(" AND su.submitid < %i" % (nextid,))

    if userid:
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))

        if not otherid:
            statement.append(m.MACRO_IGNOREUSER % (userid, "su"))

        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
    else:
        statement.append(" AND NOT su.friends_only")
    return statement


def select_count(
    userid,
    rating,
    *,
    otherid=None,
    folderid=None,
    backid=None,
    nextid=None,
    subcat=None,
    profile_page_filter=False,
    index_page_filter=False,
    featured_filter=False,
    critique_only=False,
):
    statement = "".join((
        "SELECT count(*) FROM (SELECT ",
        *_select_query(
            userid=userid,
            rating=rating,
            otherid=otherid,
            folderid=folderid,
            backid=backid,
            nextid=nextid,
            subcat=subcat,
            profile_page_filter=profile_page_filter,
            index_page_filter=index_page_filter,
            featured_filter=featured_filter,
            critique_only=critique_only,
        ),
        " LIMIT %i) t" % (COUNT_LIMIT,),
    ))
    return d.engine.scalar(statement)


def select_list(
    userid,
    rating,
    *,
    limit,
    otherid=None,
    folderid=None,
    backid=None,
    nextid=None,
    subcat=None,
    profile_page_filter=False,
    index_page_filter=False,
    featured_filter=False,
    critique_only=False,
):
    """
    Selects a list from the submissions table.

    Args:
        userid: The current user
        rating: The maximum rating level to show
        limit: The number of submissions to get
        otherid: The user whose submissions to get
        folderid: Select submissions from this folder
        backid: Select the IDs that are less than this value
        nextid: Select the IDs that are greater than this value
        subcat: Select submissions whose subcategory is within this range
            (this value + 1000)
        profile_page_filter: Do not select from folders that should not appear
            on the profile page.
        index_page_filter: Do not select from folders that should not appear on
            the front page.
        featured_filter: Select from folders marked as featured submissions and randomize the order of results.
        critique_only: Select only submissions for which critique is requested.

    Returns:
        An array with the following keys: "contype", "submitid", "title",
        "rating", "unixtime", "userid", "username", "subtype", "sub_media"
    """
    statement = "".join((
        "SELECT su.submitid, su.title, su.rating, su.unixtime, su.userid, pr.username, su.subtype ",
        *_select_query(
            userid=userid,
            rating=rating,
            otherid=otherid,
            folderid=folderid,
            backid=backid,
            nextid=nextid,
            subcat=subcat,
            profile_page_filter=profile_page_filter,
            index_page_filter=index_page_filter,
            featured_filter=featured_filter,
            critique_only=critique_only,
        ),
        " ORDER BY %s%s LIMIT %i" % ("RANDOM()" if featured_filter else "su.submitid", "" if backid else " DESC", limit),
    ))

    submissions = [{**row, "contype": 10} for row in d.engine.execute(statement)]
    media.populate_with_submission_media(submissions)

    return submissions[::-1] if backid else submissions


def select_featured(userid, otherid, rating):
    submissions = select_list(
        userid=userid,
        rating=rating,
        limit=1,
        otherid=otherid,
        featured_filter=True,
    )
    return submissions[0] if submissions else None


def select_near(userid, rating, limit, otherid, folderid, submitid):
    statement = ["""
        SELECT su.submitid, su.title, su.rating, su.unixtime, su.subtype
          FROM submission su
         WHERE su.userid = %(owner)s
               AND NOT su.hidden
    """]

    if userid:
        if d.is_sfw_mode():
            statement.append(" AND su.rating <= %(rating)s")
        else:
            # Outside of SFW mode, users always see their own content.
            statement.append(" AND (su.rating <= %%(rating)s OR su.userid = %i)" % (userid,))
        statement.append(m.MACRO_IGNOREUSER % (userid, "su"))
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))
        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
    else:
        statement.append(" AND su.rating <= %(rating)s AND NOT su.friends_only")

    if folderid:
        statement.append(" AND su.folderid = %i" % folderid)

    statement = "".join(statement)
    statement = (
        f"SELECT * FROM ({statement} AND su.submitid < %(submitid)s ORDER BY su.submitid DESC LIMIT 1) AS older"
        f" UNION ALL SELECT * FROM ({statement} AND su.submitid > %(submitid)s ORDER BY su.submitid LIMIT 1) AS newer"
    )

    username = d.get_display_name(otherid)

    query = [{
        "contype": 10,
        "userid": otherid,
        "username": username,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "subtype": i[4],
    } for i in d.engine.execute(statement, {
        "owner": otherid,
        "submitid": submitid,
        "rating": rating,
    })]

    media.populate_with_submission_media(query)

    query.sort(key=lambda i: i['submitid'])
    older = [i for i in query if i["submitid"] < submitid]
    newer = [i for i in query if i["submitid"] > submitid]

    return {
        "older": older,
        "newer": newer,
    }


def _invalidate_collectors_posts_count(submitid):
    """
    Invalidate the cached post counts of users who have as a collection the submission being edited or deleted.
    """
    owners = collection.find_owners(submitid)
    d.cached_posts_count_invalidate_multi(owners)


def edit(userid, submission, embedlink=None, friends_only=False, critique=False):
    query = d.engine.execute(
        "SELECT userid, subtype, hidden, embed_type FROM submission WHERE submitid = %(id)s",
        id=submission.submitid).first()

    if not query or query[2]:
        raise WeasylError("Unexpected")
    elif userid != query[0] and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    elif not submission.title:
        raise WeasylError("titleInvalid")
    elif not submission.rating:
        raise WeasylError("Unexpected")
    elif not folder.check(query[0], submission.folderid):
        raise WeasylError("Unexpected")
    elif submission.subtype // 1000 != query[1] // 1000:
        raise WeasylError("Unexpected")
    elif 'other' == query[3] and not embed.check_valid(embedlink):
        raise WeasylError("embedlinkInvalid")
    elif 'google-drive' == query[3]:
        embedlink = _normalize_google_docs_embed(embedlink)

    if userid == query.userid:
        profile.check_user_rating_allowed(userid, submission.rating)
        if submission.rating.minimum_age:
            profile.assert_adult(userid)

    if 'other' == query[3]:
        submission.content = "%s\n%s" % (embedlink, submission.content)

    if friends_only:
        welcome.submission_became_friends_only(submission.submitid, query.userid)

    # TODO(kailys): maintain ORM object
    db = d.connect()
    su = d.meta.tables['submission']
    q = (
        su.update()
        .values(
            folderid=submission.folderid,
            title=submission.title,
            content=submission.content,
            subtype=submission.subtype,
            rating=submission.rating,
            friends_only=friends_only,
            critique=critique,
        )
        .where(su.c.submitid == submission.submitid))
    db.execute(q)

    if 'google-drive' == query[3]:
        db = d.connect()
        gde = d.meta.tables['google_doc_embeds']
        q = (gde.update()
             .values(embed_url=embedlink)
             .where(gde.c.submitid == submission.submitid))
        db.execute(q)

    if userid != query[0]:
        from weasyl import moderation
        moderation.note_about(
            userid, query[0], 'The following submission was edited:',
            '- ' + text.markdown_link(submission.title, '/submission/%s?anyway=true' % (submission.submitid,)))

    # possible rating change
    d.cached_posts_count.invalidate(query[0])
    _invalidate_collectors_posts_count(submission.submitid)


def remove(userid, submitid):
    ownerid = d.get_ownerid(submitid=submitid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    query = d.execute("UPDATE submission SET hidden = TRUE"
                      " WHERE submitid = %i AND NOT hidden RETURNING submitid", [submitid])

    if query:
        welcome.submission_remove(submitid)
        d.cached_posts_count.invalidate(ownerid)
        _invalidate_collectors_posts_count(submitid)

    return ownerid


def reupload_cover(userid, submitid, coverfile):
    query = d.engine.execute(
        "SELECT userid, subtype FROM submission WHERE submitid = %(id)s",
        id=submitid).first()

    if not query:
        raise WeasylError("Unexpected")
    elif userid not in staff.MODS and userid != query[0]:
        raise WeasylError("Unexpected")
    elif query[1] < 2000:
        raise WeasylError("Unexpected")

    cover_media_item = media.make_cover_media_item(coverfile)
    if not cover_media_item:
        orm.SubmissionMediaLink.clear_link(submitid, 'cover')
    else:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)


@region.cache_on_arguments(expiration_time=600)
@d.record_timing
def select_recently_popular():
    """
    Get a list of recent, popular submissions.

    To calculate scores, this method performs the following evaluation:

    item_score = log(item_fave_count + 1) + log(item_view_counts) / 2 + submission_time / 180000

    180000 is roughly two days. So intuitively an item two days old needs an order of
    magnitude more favorites/views compared to a fresh one. Also the favorites are
    quadratically more influential than views. The result is that this algorithm favors
    recent, heavily favorited items.

    :return: A list of submission dictionaries, in score-rank order.
    """
    query = d.engine.execute("""
        SELECT
            submission.submitid,
            submission.title,
            submission.rating,
            submission.subtype,
            submission_tags.tags,
            submission.userid,
            profile.username
        FROM submission
            INNER JOIN submission_tags ON submission.submitid = submission_tags.submitid
            INNER JOIN profile ON submission.userid = profile.userid
        WHERE
            NOT submission.hidden
            AND NOT submission.friends_only
        ORDER BY
            log(submission.favorites + 1) +
                log(submission.page_views + 1) / 2 +
                submission.unixtime / 180000.0
                DESC
        LIMIT 128
    """)

    submissions = [{**row, "contype": 10} for row in query]
    media.populate_with_submission_media(submissions)
    media.strip_non_thumbnail_media(submissions)

    return submissions


@region.cache_on_arguments(expiration_time=600)
def select_critique():
    query = d.engine.execute("""
        SELECT
            submission.submitid,
            submission.title,
            submission.rating,
            submission.subtype,
            submission_tags.tags,
            submission.userid,
            profile.username
        FROM submission
            INNER JOIN submission_tags ON submission.submitid = submission_tags.submitid
            INNER JOIN profile ON submission.userid = profile.userid
        WHERE
            NOT submission.hidden
            AND NOT submission.friends_only
            AND submission.critique
        ORDER BY submission.submitid DESC
        LIMIT 128
    """)

    submissions = [{**row, "contype": 10} for row in query]
    media.populate_with_submission_media(submissions)
    media.strip_non_thumbnail_media(submissions)

    return submissions

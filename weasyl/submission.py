from __future__ import absolute_import, division

import urlparse
from io import BytesIO

from akismet import SpamStatus
import arrow
import sqlalchemy as sa

from libweasyl.cache import region
from libweasyl import (
    html,
    images,
    images_new,
    ratings,
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
from weasyl import spam_filtering
from weasyl import welcome
from weasyl.error import WeasylError


_MEGABYTE = 1048576

_LIMITS = {
    ".jpg": 10 * _MEGABYTE,
    ".png": 10 * _MEGABYTE,
    ".gif": 10 * _MEGABYTE,
    ".txt": 2 * _MEGABYTE,
    ".pdf": 10 * _MEGABYTE,
    ".htm": 10 * _MEGABYTE,
    ".mp3": 15 * _MEGABYTE,
    ".swf": 15 * _MEGABYTE,
}


def _limit(size, extension):
    """
    Return True if the file size exceeds the limit designated to the specified
    file type, else False.
    """
    limit = _LIMITS[extension]
    return size > limit


def _create_notifications(userid, submitid, rating, settings, title, tags):
    """
    Creates notifications to watchers.
    """
    welcome.submission_insert(userid, submitid, rating=rating.code, settings=settings)


def _check_for_spam(submission, userid):
    """
    Queries the spam filtering backend to determine if the submitted content is spam.

    Implementation note: Since this raises WeasylError if it is blatantly spam, call this _before_ writing out to the
    database or making any saves to disk.

    :param submission:
    :param userid:
    :return: Boolean False if the textual content submitted is not considered spam (or if an unknown Akismet response
    is returned), or Boolean True if it the item is probably spam.
    :raises WeasylError("SpamFilteringDropped"): If the submitted textual content is blatantly spam.
    """
    # Run the journal through Akismet to check for spam
    is_spam = False
    if spam_filtering.FILTERING_ENABLED:
        result = spam_filtering.check(
            user_ip=submission.submitter_ip_address,
            user_agent_id=submission.submitter_user_agent_id,
            user_id=userid,
            comment_type="journal",
            comment_content=submission.content,
        )
        if result == SpamStatus.DefiniteSpam:
            raise WeasylError("SpamFilteringDropped")
        elif result == SpamStatus.ProbableSpam:
            is_spam = True
    return is_spam


def check_for_duplicate_media(userid, mediaid):
    db = d.connect()
    q = (
        db.query(orm.Submission)
        .filter_by(userid=userid, is_hidden=False)
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

            newid = create_specific(
                userid=userid,
                submission=submission,
                **kwargs)
            if newid:
                p = d.meta.tables['profile']
                d.connect().execute(p.update().where(p.c.userid == userid).values(latest_submission_time=arrow.utcnow()))
            return newid

        return create_generic

    return wrapper


@_create_submission(expected_type=1)
def create_visual(userid, submission,
                  friends_only, tags, imageURL, thumbfile,
                  submitfile, critique, create_notifications):
    if imageURL:
        resp = d.http_get(imageURL, timeout=5)
        submitfile = resp.content

    # Determine filesizes
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    if not submitsize:
        raise WeasylError("submitSizeZero")
    elif thumbsize > 10 * _MEGABYTE:
        raise WeasylError("thumbSizeExceedsLimit")

    im = image.from_string(submitfile)
    submitextension = image.image_extension(im)
    if submitextension not in [".jpg", ".png", ".gif"]:
        raise WeasylError("submitType")
    if _limit(submitsize, submitextension):
        raise WeasylError("submitSizeExceedsLimit")

    # Check if the submission is spam
    is_spam = _check_for_spam(submission=submission, userid=userid)

    submit_file_type = submitextension.lstrip('.')
    submit_media_item = orm.fetch_or_create_media_item(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    cover_media_item = submit_media_item.ensure_cover_image(im)

    # Thumbnail stuff.
    # Always create a 'generated' thumbnail from the source image.
    with BytesIO(submitfile) as buf:
        thumbnail_formats = images_new.get_thumbnail(buf)

    thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.compatible
    thumb_generated_media_item = orm.fetch_or_create_media_item(
        thumb_generated,
        file_type=thumb_generated_file_type,
        attributes=thumb_generated_attributes,
    )

    if thumbnail_formats.webp is None:
        thumb_generated_media_item_webp = None
    else:
        thumb_generated, thumb_generated_file_type, thumb_generated_attributes = thumbnail_formats.webp
        thumb_generated_media_item_webp = orm.fetch_or_create_media_item(
            thumb_generated,
            file_type=thumb_generated_file_type,
            attributes=thumb_generated_attributes,
        )

    # If requested, also create a 'custom' thumbnail.
    thumb_media_item = media.make_cover_media_item(thumbfile)
    if thumb_media_item:
        thumb_custom = images.make_thumbnail(image.from_string(thumbfile))
        thumb_custom_media_item = orm.fetch_or_create_media_item(
            thumb_custom.to_buffer(format=submit_file_type), file_type=submit_file_type,
            im=thumb_custom)

    # Assign settings
    settings = []
    settings.append("f" if friends_only else "")
    settings.append("q" if critique else "")
    settings = "".join(settings)

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
            "settings": settings,
            "favorites": 0,
            "sorttime": now,
            "is_spam": is_spam,
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
    searchtag.associate(userid, tags, submitid=submitid)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, settings,
                              submission.title, tags)

    d.metric('increment', 'submissions')
    d.metric('increment', 'visualsubmissions')

    return submitid


def check_google_doc_embed_data(embedlink):
    m = text.url_regexp.search(embedlink)
    if not m:
        raise WeasylError('googleDocsEmbedLinkInvalid')
    embedlink = m.group()
    parsed = urlparse.urlparse(embedlink)
    if parsed.scheme != 'https' or parsed.netloc != 'docs.google.com':
        raise WeasylError('googleDocsEmbedLinkInvalid')


@_create_submission(expected_type=2)
def create_literary(userid, submission, embedlink=None, friends_only=False, tags=None,
                    coverfile=None, thumbfile=None, submitfile=None, critique=False,
                    create_notifications=True):
    if embedlink:
        check_google_doc_embed_data(embedlink)

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
        submit_media_item = orm.fetch_or_create_media_item(
            submitfile, file_type=submitextension.lstrip('.'))
        check_for_duplicate_media(userid, submit_media_item.mediaid)
    else:
        submit_media_item = None

    # Check if the submission is spam
    is_spam = _check_for_spam(submission=submission, userid=userid)

    thumb_media_item = media.make_cover_media_item(thumbfile)
    cover_media_item = media.make_cover_media_item(coverfile)
    if cover_media_item and not thumb_media_item:
        thumb_media_item = cover_media_item

    # Assign settings
    settings = []
    settings.append("f" if friends_only else "")
    settings.append("q" if critique else "")
    if embedlink:
        settings.append('D')
    settings = "".join(settings)

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
            "settings": settings,
            "favorites": 0,
            "sorttime": now,
            "is_spam": is_spam,
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
    searchtag.associate(userid, tags, submitid=submitid)

    if submit_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'submission', submit_media_item)
    if cover_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)
    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, settings,
                              submission.title, tags)

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
        submit_media_item = orm.fetch_or_create_media_item(
            submitfile, file_type=submitextension.lstrip('.'))
        check_for_duplicate_media(userid, submit_media_item.mediaid)
    else:
        submit_media_item = None

    # Check if the submission is spam
    is_spam = _check_for_spam(submission=submission, userid=userid)

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
        tempthumb_media_item = orm.fetch_or_create_media_item(
            tempthumb.to_buffer(format=tempthumb_type),
            file_type=tempthumb_type,
            im=tempthumb)

    # Assign settings
    settings = []
    settings.append("f" if friends_only else "")
    settings.append("q" if critique else "")
    settings.append("v" if embedlink else "")
    settings = "".join(settings)

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
            "settings": settings,
            "favorites": 0,
            "sorttime": now,
            "is_spam": is_spam,
            "submitter_ip_address": submission.submitter_ip_address,
            "submitter_user_agent_id": submission.submitter_user_agent_id,
        }])
        .returning(d.meta.tables['submission'].c.submitid))
    submitid = db.scalar(q)

    # Assign search tags
    searchtag.associate(userid, tags, submitid=submitid)

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
        _create_notifications(userid, submitid, submission.rating, settings,
                              submission.title, tags)

    d.metric('increment', 'submissions')
    d.metric('increment', 'multimediasubmissions')

    return submitid, bool(thumb_media_item)


def reupload(userid, submitid, submitfile):
    submitsize = len(submitfile)

    # Select submission data
    query = d.engine.execute(
        "SELECT userid, subtype, settings FROM submission WHERE submitid = %(id)s AND settings !~ 'h'",
        id=submitid,
    ).first()

    if not query:
        raise WeasylError("Unexpected")
    elif userid != query[0]:
        raise WeasylError("Unexpected")
    elif "v" in query[2] or "D" in query[2]:
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
    submit_media_item = orm.fetch_or_create_media_item(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    orm.SubmissionMediaLink.make_or_replace_link(submitid, 'submission', submit_media_item)

    if subcat == m.ART_SUBMISSION_CATEGORY:
        cover_media_item = submit_media_item.ensure_cover_image()
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'cover', cover_media_item)
        generated_thumb = images.make_thumbnail(im)
        generated_thumb_media_item = orm.fetch_or_create_media_item(
            generated_thumb.to_buffer(format=images.image_file_type(generated_thumb)),
            file_type=submit_file_type,
            im=generated_thumb)
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-generated', generated_thumb_media_item)


def select_view(userid, submitid, rating, ignore=True, anyway=None):
    query = d.engine.execute("""
        SELECT
            su.userid, pr.username, su.folderid, su.unixtime, su.title, su.content, su.subtype, su.rating, su.settings,
            su.page_views, fd.title, su.favorites
        FROM submission su
            INNER JOIN profile pr USING (userid)
            LEFT JOIN folder fd USING (folderid)
        WHERE su.submitid = %(id)s
    """, id=submitid).first()

    # Sanity check
    if query and userid in staff.MODS and anyway == "true":
        pass
    elif not query or "h" in query[8]:
        raise WeasylError("submissionRecordMissing")
    elif query[7] > rating and ((userid != query[0] and userid not in staff.MODS) or d.is_sfw_mode()):
        raise WeasylError("RatingExceeded")
    elif "f" in query[8] and not frienduser.check(userid, query[0]):
        raise WeasylError("FriendsOnly")
    elif ignore and ignoreuser.check(userid, query[0]):
        raise WeasylError("UserIgnored")
    elif ignore and blocktag.check(userid, submitid=submitid):
        raise WeasylError("TagBlocked")

    # Get submission filename
    submitfile = media.get_submission_media(submitid).get('submission', [None])[0]

    # Get submission text
    if submitfile and submitfile['file_type'] in ['txt', 'htm']:
        submittext = files.read(submitfile['full_file_path'])
    else:
        submittext = None

    embedlink = d.text_first_line(query[5]) if "v" in query[8] else None

    google_doc_embed = None
    if 'D' in query[8]:
        db = d.connect()
        gde = d.meta.tables['google_doc_embeds']
        q = (sa.select([gde.c.embed_url])
             .where(gde.c.submitid == submitid))
        results = db.execute(q).fetchall()
        if not results:
            raise WeasylError("can't find embed information")
        google_doc_embed = results[0]

    tags, artist_tags = searchtag.select_with_artist_tags(submitid)
    settings = d.get_profile_settings(query[0])

    fave_count = query[11]

    if fave_count is None:
        fave_count = d.engine.scalar(
            "SELECT COUNT(*) FROM favorite WHERE (targetid, type) = (%(target)s, 's')",
            target=submitid)

    return {
        "submitid": submitid,
        "userid": query[0],
        "username": query[1],
        "folderid": query[2],
        "unixtime": query[3],
        "title": query[4],
        "content": (d.text_first_line(query[5], strip=True) if "v" in query[8] else query[5]),
        "subtype": query[6],
        "rating": query[7],
        "settings": query[8],
        "page_views": (
            query[9] + 1 if d.common_view_content(userid, 0 if anyway == "true" else submitid, "submit") else query[9]),
        "fave_count": fave_count,


        "mine": userid == query[0],
        "reported": report.check(submitid=submitid),
        "favorited": favorite.check(userid, submitid=submitid),
        "friends_only": "f" in query[8],
        "hidden_submission": "h" in query[8],
        "collected": collection.owns(userid, submitid),
        "no_request": not settings.allow_collection_requests,

        "text": submittext,
        "sub_media": media.get_submission_media(submitid),
        "user_media": media.get_user_media(query[0]),
        "submit": submitfile,
        "embedlink": embedlink,
        "embed": embed.html(embedlink) if embedlink is not None else None,
        "google_doc_embed": google_doc_embed,


        "tags": tags,
        "artist_tags": artist_tags,
        "removable_tags": searchtag.removable_tags(userid, query[0], tags, artist_tags),
        "can_remove_tags": searchtag.can_remove_tags(userid, query[0]),
        "folder_more": select_near(userid, rating, 1, query[0], query[2], submitid),
        "folder_title": query[10] if query[10] else "Root",


        "comments": comment.select(userid, submitid=submitid),
    }


def select_view_api(userid, submitid, anyway=False, increment_views=False):
    rating = d.get_rating(userid)
    db = d.connect()
    sub = db.query(orm.Submission).get(submitid)
    if sub is None or 'hidden' in sub.settings:
        raise WeasylError("submissionRecordMissing")
    sub_rating = sub.rating.code
    if 'friends-only' in sub.settings and not frienduser.check(userid, sub.userid):
        raise WeasylError("submissionRecordMissing")
    elif sub_rating > rating and userid != sub.userid:
        raise WeasylError("RatingExceeded")
    elif not anyway and ignoreuser.check(userid, sub.userid):
        raise WeasylError("UserIgnored")
    elif not anyway and blocktag.check(userid, submitid=submitid):
        raise WeasylError("TagBlocked")

    description = sub.content
    embedlink = None
    if 'embedded-content' in sub.settings:
        embedlink, _, description = description.partition('\n')
    elif 'gdocs-embed' in sub.settings:
        embedlink = sub.google_doc_embed.embed_url

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
        'favorites': favorite.count(submitid),
        'comments': comment.count(submitid),
        'favorited': favorite.check(userid, submitid=submitid),
        'friends_only': 'friends-only' in sub.settings,
    }


def twitter_card(request, submitid):
    query = d.engine.execute("""
        SELECT
            su.title, su.settings, su.content, su.subtype, su.userid, pr.username, pr.full_name, pr.config, ul.link_value, su.rating
        FROM submission su
            INNER JOIN profile pr USING (userid)
            LEFT JOIN user_links ul ON su.userid = ul.userid AND ul.link_type = 'twitter'
        WHERE submitid = %(id)s
        LIMIT 1
    """, id=submitid).first()

    if not query:
        raise WeasylError("submissionRecordMissing")
    title, settings, content, subtype, userid, username, full_name, config, twitter, rating = query
    if 'h' in settings:
        raise WeasylError("submissionRecordMissing")
    elif 'f' in settings:
        raise WeasylError("FriendsOnly")

    if 'v' in settings:
        content = d.text_first_line(content, strip=True)
    content = d.summarize(html.strip_html(content))
    if not content:
        content = "[This submission has no description.]"

    ret = {
        'url': d.absolutify_url(
            request.route_path(
                'submission_detail_profile',
                name=d.get_sysname(username),
                submitid=submitid,
                slug=text.slug_for(title),
            )
        ),
    }

    if twitter:
        ret['creator'] = '@%s' % (twitter.lstrip('@'),)
        ret['title'] = title
    else:
        ret['title'] = '%s by %s' % (title, full_name)

    if ratings.CODE_MAP[rating].minimum_age >= 18:
        ret['card'] = 'summary'
        ret['description'] = 'This image is rated 18+ and only viewable on weasyl.com'
        return ret

    ret['description'] = content

    subcat = subtype // 1000 * 1000
    media_items = media.get_submission_media(submitid)
    if subcat == m.ART_SUBMISSION_CATEGORY and media_items.get('submission'):
        ret['card'] = 'photo'
        ret['image:src'] = d.absolutify_url(media_items['submission'][0]['display_url'])
    else:
        ret['card'] = 'summary'
        thumb = media_items.get('thumbnail-custom') or media_items.get('thumbnail-generated')
        if thumb:
            ret['image:src'] = d.absolutify_url(thumb[0]['display_url'])

    return ret


def select_query(userid, rating, otherid=None, folderid=None,
                 backid=None, nextid=None, subcat=None, exclude=None,
                 options=[], profile_page_filter=False,
                 index_page_filter=False, featured_filter=False):
    statement = [
        "FROM submission su "
        "INNER JOIN profile pr ON su.userid = pr.userid "
        "LEFT JOIN folder f USING (folderid) "
        "WHERE su.settings !~ 'h'"]
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

    if exclude:
        statement.append(" AND su.submitid != %i" % (exclude,))

    if subcat:
        statement.append(" AND su.subtype >= %i AND su.subtype < %i" % (subcat, subcat + 1000))

    if "critique" in options:
        statement.append(" AND su.settings ~ 'q' AND su.unixtime > %i" % (d.get_time() - 259200,))

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
        statement.append(" AND su.settings !~ 'f'")
    return statement


def select_count(userid, rating, otherid=None, folderid=None,
                 backid=None, nextid=None, subcat=None, exclude=None,
                 options=[], profile_page_filter=False,
                 index_page_filter=False, featured_filter=False):
    if options not in [[], ['critique'], ['randomize']]:
        raise ValueError("Unexpected options: %r" % (options,))

    statement = ["SELECT COUNT(submitid) "]
    statement.extend(select_query(
        userid, rating, otherid, folderid, backid, nextid, subcat, exclude, options, profile_page_filter,
        index_page_filter, featured_filter))
    return d.execute("".join(statement))[0][0]


def select_list(userid, rating, limit, otherid=None, folderid=None,
                backid=None, nextid=None, subcat=None, exclude=None,
                options=[], profile_page_filter=False,
                index_page_filter=False, featured_filter=False):
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
        exclude: Exclude this specific submission ID
        options: List that can contain the following values:
            "critique": Submissions flagged for critique; additionally selects
                submissions newer than 3 days old
            "randomize": Randomize the ordering of the results
        profile_page_filter: Do not select from folders that should not appear
            on the profile page.
        index_page_filter: Do not select from folders that should not appear on
            the front page.
        featured_filter: Select from folders marked as featured submissions.

    Returns:
        An array with the following keys: "contype", "submitid", "title",
        "rating", "unixtime", "userid", "username", "subtype", "sub_media"
    """
    if options not in [[], ['critique'], ['randomize']]:
        raise ValueError("Unexpected options: %r" % (options,))

    randomize = bool(options)

    statement = [
        "SELECT su.submitid, su.title, su.rating, su.unixtime, "
        "su.userid, pr.username, su.settings, su.subtype "]

    statement.extend(select_query(
        userid, rating, otherid, folderid, backid, nextid, subcat, exclude, options, profile_page_filter,
        index_page_filter, featured_filter))

    statement.append(
        " ORDER BY %s%s LIMIT %i" % ("RANDOM()" if randomize else "su.submitid", "" if backid else " DESC", limit))

    query = [{
        "contype": 10,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "subtype": i[7],
    } for i in d.execute("".join(statement))]
    media.populate_with_submission_media(query)

    return query[::-1] if backid else query


def select_featured(userid, otherid, rating):
    submissions = select_list(
        userid, rating, limit=1, otherid=otherid,
        options=['randomize'], featured_filter=True)
    return None if not submissions else submissions[0]


def select_near(userid, rating, limit, otherid, folderid, submitid):
    statement = ["""
        SELECT su.submitid, su.title, su.rating, su.unixtime, su.userid,
               pr.username, su.settings, su.subtype
          FROM submission su
         INNER JOIN profile pr ON su.userid = pr.userid
         WHERE su.userid = %i
               AND su.settings !~ 'h'
    """ % (otherid,)]

    if userid:
        # Users always see their own content.
        statement.append(" AND (su.rating <= %i OR su.userid = %i)" % (rating, userid))
        statement.append(m.MACRO_IGNOREUSER % (userid, "su"))
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))
        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
    else:
        statement.append(" AND su.rating <= %i AND su.settings !~ 'f'" % (rating,))

    if folderid:
        statement.append(" AND su.folderid = %i" % folderid)

    query = [{
        "contype": 10,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "subtype": i[7],
    } for i in d.execute("".join(statement))]

    query.sort(key=lambda i: i['submitid'])
    older = [i for i in query if i["submitid"] < submitid][-limit:]
    newer = [i for i in query if i["submitid"] > submitid][:limit]
    media.populate_with_submission_media(older + newer)

    return {
        "older": older,
        "newer": newer,
    }


def edit(userid, submission, embedlink=None, friends_only=False, critique=False):
    query = d.engine.execute(
        "SELECT userid, subtype, settings FROM submission WHERE submitid = %(id)s",
        id=submission.submitid).first()

    if not query or "h" in query[2]:
        raise WeasylError("Unexpected")
    elif "a" in query[2] and userid not in staff.MODS:
        raise WeasylError("AdminLocked")
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
    elif 'v' in query[2] and not embed.check_valid(embedlink):
        raise WeasylError("embedlinkInvalid")
    elif 'D' in query[2]:
        check_google_doc_embed_data(embedlink)
    profile.check_user_rating_allowed(userid, submission.rating)

    # Assign settings
    settings = [query[2].replace("f", "").replace("q", "")]
    settings.append("f" if friends_only else "")
    settings.append("q" if critique else "")
    settings = "".join(settings)

    if "v" in settings:
        submission.content = "%s\n%s" % (embedlink, submission.content)

    if "f" in settings:
        welcome.submission_became_friends_only(submission.submitid, userid)

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
            settings=settings,
        )
        .where(su.c.submitid == submission.submitid))
    db.execute(q)

    if 'D' in settings:
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


def remove(userid, submitid):
    ownerid = d.get_ownerid(submitid=submitid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    query = d.execute("UPDATE submission SET settings = settings || 'h'"
                      " WHERE submitid = %i AND settings !~ 'h' RETURNING submitid", [submitid])

    if query:
        welcome.submission_remove(submitid)

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


@region.cache_on_arguments()
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
            log(submission.favorites + 1) +
                log(submission.page_views + 1) / 2 +
                submission.unixtime / 180000.0 AS score,
            submission.submitid,
            submission.title,
            submission.rating,
            submission.subtype,
            submission.unixtime,
            submission_tags.tags,
            submission.userid,
            profile.username
        FROM submission
            INNER JOIN submission_tags ON submission.submitid = submission_tags.submitid
            INNER JOIN profile ON submission.userid = profile.userid
        WHERE
            submission.settings !~ '[hf]'
            AND submission.favorites IS NOT NULL
        ORDER BY score DESC
        LIMIT 128
    """)

    submissions = [dict(row, contype=10) for row in query]
    media.populate_with_submission_media(submissions)
    return submissions

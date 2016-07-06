# submission.py

import urlparse

import arrow
import sqlalchemy as sa

from error import PostgresError, WeasylError
import macro as m
import define as d

import files

import embed
import image
import folder
import report
import comment
import profile
import welcome
import blocktag
import favorite
import searchtag
import frienduser
import ignoreuser
import collection

from libweasyl.cache import region
from libweasyl import html, images, text, ratings, staff

from weasyl import api, media, orm, twits


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


def _limit(size, extension, premium):
    """
    Return True if the file size exceeds the limit designated to the specified
    file type, else False.
    """
    limit = _LIMITS.get(extension)

    if limit is None:
        return None
    else:
        return size > limit


def _create_notifications(userid, submitid, rating, settings, title, tags):
    """
    Creates notifications to welcome page, watchers, Twitter.
    """
    welcome.submission_insert(userid, submitid, rating=rating.code, settings=settings)

    if 'q' in settings and 'f' not in settings:
        _post_to_twitter_about(submitid, title, rating.code, tags)


def _post_to_twitter_about(submitid, title, rating, tags):
    url = d.absolutify_url('/submission/%s/%s' % (submitid, text.slug_for(title)))

    st = d.meta.tables['searchtag']
    sms = d.meta.tables['searchmapsubmit']
    q = (sa.select([st.c.title])
         .select_from(st.join(sms, st.c.tagid == sms.c.tagid))
         .where(st.c.title.in_(t.lower() for t in tags))
         .group_by(st.c.title)
         .order_by(sa.func.count().desc()))

    account = 'WeasylCritique'
    if rating in (ratings.MATURE.code, ratings.EXPLICIT.code):
        account = 'WZLCritiqueNSFW'
    length = 26
    selected_tags = []
    db = d.connect()
    for tag, in db.execute(q):
        if len(tag) + 2 + length > 140:
            break
        selected_tags.append('#' + tag)
        length += len(tag) + 2

    twits.post(account, u'%s %s' % (url, ' '.join(selected_tags)))


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

            return create_specific(
                userid=userid,
                submission=submission,
                **kwargs)

        return create_generic

    return wrapper


@_create_submission(expected_type=1)
def create_visual(userid, submission,
                  friends_only, tags, imageURL, thumbfile,
                  submitfile, critique, create_notifications):
    premium = d.get_premium(userid)

    if imageURL:
        resp = d.http_get(imageURL, timeout=5)
        submitfile = resp.content

    # Determine filesizes
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    if not submitsize:
        files.clear_temporary(userid)
        raise WeasylError("submitSizeZero")
    elif thumbsize > 10 * _MEGABYTE:
        files.clear_temporary(userid)
        raise WeasylError("thumbSizeExceedsLimit")

    im = image.from_string(submitfile)
    submitextension = image.image_extension(im)
    if _limit(submitsize, submitextension, premium):
        raise WeasylError("submitSizeExceedsLimit")
    elif submitextension not in [".jpg", ".png", ".gif"]:
        raise WeasylError("submitType")
    submit_file_type = submitextension.lstrip('.')
    submit_media_item = orm.fetch_or_create_media_item(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    cover_media_item = submit_media_item.ensure_cover_image(im)

    # Thumbnail stuff.
    # Always create a 'generated' thumbnail from the source image.
    thumb_generated = images.make_thumbnail(im)
    if thumb_generated is im:
        thumb_generated_media_item = submit_media_item
    else:
        thumb_generated_media_item = orm.fetch_or_create_media_item(
            thumb_generated.to_buffer(format=submit_file_type), file_type=submit_file_type,
            im=thumb_generated)
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
            "sorttime": now,
        }]).returning(d.meta.tables['submission'].c.submitid))
    submitid = db.scalar(q)

    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'submission', submit_media_item)
    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'cover', cover_media_item)
    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'thumbnail-generated', thumb_generated_media_item)
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
    premium = d.get_premium(userid)

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
        if _limit(submitsize, submitextension, premium):
            raise WeasylError("submitSizeExceedsLimit")
        submit_media_item = orm.fetch_or_create_media_item(
            submitfile, file_type=submitextension.lstrip('.'))
        check_for_duplicate_media(userid, submit_media_item.mediaid)
    else:
        submit_media_item = None

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
    try:
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
                "sorttime": now,
            }])
            .returning(d.meta.tables['submission'].c.submitid))
        submitid = db.scalar(q)
        if embedlink:
            q = (d.meta.tables['google_doc_embeds'].insert()
                 .values(submitid=submitid, embed_url=embedlink))
            db.execute(q)
    except:
        files.clear_temporary(userid)
        raise

    # Assign search tags
    searchtag.associate(userid, tags, submitid=submitid)

    if submit_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'submission', submit_media_item, rating=submission.rating.code)
    if cover_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'cover', cover_media_item, rating=submission.rating.code)
    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, settings,
                              submission.title, tags)

    # Clear temporary files
    files.clear_temporary(userid)

    d.metric('increment', 'submissions')
    d.metric('increment', 'literarysubmissions')

    return submitid, bool(thumb_media_item)


@_create_submission(expected_type=3)
def create_multimedia(userid, submission, embedlink=None, friends_only=None,
                      tags=None, coverfile=None, thumbfile=None, submitfile=None,
                      critique=False, create_notifications=True, auto_thumb=False):
    premium = d.get_premium(userid)
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
        elif _limit(submitsize, submitextension, premium):
            raise WeasylError("submitSizeExceedsLimit")
        submit_media_item = orm.fetch_or_create_media_item(
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
    try:
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
                "sorttime": now,
            }])
            .returning(d.meta.tables['submission'].c.submitid))
        submitid = db.scalar(q)
    except PostgresError:
        files.clear_temporary(userid)
        raise

    # Assign search tags
    searchtag.associate(userid, tags, submitid=submitid)

    if submit_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'submission', submit_media_item, rating=submission.rating.code)
    if cover_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'cover', cover_media_item, rating=submission.rating.code)
    if thumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-source', thumb_media_item)
    if tempthumb_media_item:
        orm.SubmissionMediaLink.make_or_replace_link(submitid, 'thumbnail-custom',
                                                     tempthumb_media_item)

    # Create notifications
    if create_notifications:
        _create_notifications(userid, submitid, submission.rating, settings,
                              submission.title, tags)

    # Clear temporary files
    files.clear_temporary(userid)

    d.metric('increment', 'submissions')
    d.metric('increment', 'multimediasubmissions')

    return submitid, bool(thumb_media_item)


def reupload(userid, submitid, submitfile):
    submitsize = len(submitfile)

    # Select submission data
    query = d.execute("SELECT userid, subtype, settings, rating FROM submission WHERE submitid = %i AND settings !~ 'h'",
                      [submitid], ["single"])

    if not query:
        raise WeasylError("Unexpected")
    elif userid != query[0]:
        raise WeasylError("Unexpected")
    elif "v" in query[2] or "D" in query[2]:
        raise WeasylError("Unexpected")

    subcat = query[1] / 1000 * 1000
    if subcat not in m.ALL_SUBMISSION_CATEGORIES:
        raise WeasylError("Unexpected")
    premium = d.get_premium(userid)

    # Check invalid file data
    if not submitsize:
        files.clear_temporary(userid)
        raise WeasylError("submitSizeZero")

    # Write temporary submission file
    submitextension = files.get_extension_for_category(submitfile, subcat)
    if submitextension is None:
        raise WeasylError("submitType")
    elif subcat == m.ART_SUBMISSION_CATEGORY and submitextension not in [".jpg", ".png", ".gif"]:
        raise WeasylError("submitType")
    elif subcat == m.MULTIMEDIA_SUBMISSION_CATEGORY and submitextension not in [".mp3", ".swf"]:
        raise WeasylError("submitType")
    elif _limit(submitsize, submitextension, premium):
        raise WeasylError("submitSizeExceedsLimit")

    submit_file_type = submitextension.lstrip('.')
    im = None
    if submit_file_type in {'jpg', 'png', 'gif'}:
        im = image.from_string(submitfile)
    submit_media_item = orm.fetch_or_create_media_item(
        submitfile, file_type=submit_file_type, im=im)
    check_for_duplicate_media(userid, submit_media_item.mediaid)
    orm.SubmissionMediaLink.make_or_replace_link(
        submitid, 'submission', submit_media_item, rating=query[3])

    if subcat == m.ART_SUBMISSION_CATEGORY:
        cover_media_item = submit_media_item.ensure_cover_image()
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'cover', cover_media_item, rating=query[3])
        generated_thumb = images.make_thumbnail(im)
        generated_thumb_media_item = orm.fetch_or_create_media_item(
            generated_thumb.to_buffer(format=images.image_file_type(generated_thumb)),
            file_type=submit_file_type,
            im=generated_thumb)
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'thumbnail-generated', generated_thumb_media_item, rating=query[3])


def is_hidden(submitid):
    db = d.connect()
    su = d.meta.tables['submission']
    q = d.sa.select([su.c.settings.op('~')('h')]).where(su.c.submitid == submitid)
    results = db.execute(q).fetchall()
    return bool(results and results[0][0])


def select_view(userid, submitid, rating, ignore=True, anyway=None):
    query = d.execute("""
        SELECT
            su.userid, pr.username, su.folderid, su.unixtime, su.title, su.content, su.subtype, su.rating, su.settings,
            su.page_views, su.sorttime, pr.config, fd.title
        FROM submission su
            INNER JOIN profile pr USING (userid)
            LEFT JOIN folder fd USING (folderid)
        WHERE su.submitid = %i
    """, [submitid], options=["single", "list"])

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
        "fave_count": d.execute(
            "SELECT COUNT(*) FROM favorite WHERE (targetid, type) = (%i, 's')",
            [submitid], ["element"]),


        "mine": userid == query[0],
        "reported": report.check(submitid=submitid),
        "favorited": favorite.check(userid, submitid=submitid),
        "friends_only": "f" in query[8],
        "hidden_submission": "h" in query[8],
        "collectors": collection.find_owners(submitid),
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
        "folder_title": query[12] if query[12] else "Root",


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


def twitter_card(submitid):
    query = d.execute("""
        SELECT
            su.title, su.settings, su.content, su.subtype, su.userid, pr.username, pr.full_name, pr.config, ul.link_value, su.rating
        FROM submission su
            INNER JOIN profile pr USING (userid)
            LEFT JOIN user_links ul ON su.userid = ul.userid AND ul.link_type = 'twitter'
        WHERE submitid = %i
        LIMIT 1
    """, [submitid], ["single"])

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
            '/submission/%s/%s' % (submitid, text.slug_for(title))),
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

    subcat = subtype / 1000 * 1000
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
                 options=[], config=None, profile_page_filter=False,
                 index_page_filter=False, featured_filter=False):
    if config is None:
        config = d.get_config(userid)
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
    elif "offset" in options:
        statement.append(" AND su.unixtime < %i" % (d.get_time() - 1800,))

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
                 options=[], config=None, profile_page_filter=False,
                 index_page_filter=False, featured_filter=False):
    statement = ["SELECT COUNT(submitid) "]
    statement.extend(select_query(
        userid, rating, otherid, folderid, backid, nextid, subcat, exclude, options, config, profile_page_filter,
        index_page_filter, featured_filter))
    return d.execute("".join(statement))[0][0]


def select_list(userid, rating, limit, otherid=None, folderid=None,
                backid=None, nextid=None, subcat=None, exclude=None,
                options=[], config=None, profile_page_filter=False,
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
            "encore": Order results by sort time rather than submission id
            "offset": Select submissions older than half an hour
        config: Database config override
        profile_page_filter: Do not select from folders that should not appear
            on the profile page.
        index_page_filter: Do not select from folders that should not appear on
            the front page.
        featured_filter: Select from folders marked as featured submissions.

    Returns:
        An array with the following keys: "contype", "submitid", "title",
        "rating", "unixtime", "userid", "username", "subtype", "sub_media"
    """

    statement = [
        "SELECT su.submitid, su.title, su.rating, su.unixtime, "
        "su.userid, pr.username, su.settings, su.subtype "]

    statement.extend(select_query(
        userid, rating, otherid, folderid, backid, nextid, subcat, exclude, options, config, profile_page_filter,
        index_page_filter, featured_filter))

    statement.append(
        " ORDER BY %s%s LIMIT %i" % ("RANDOM()" if "critique" in options or "randomize" in options else
                                     "su.sorttime" if "encore" in options else
                                     "su.submitid", "" if backid else " DESC", limit))

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
        options=['randomize', 'cover'], featured_filter=True)
    return None if not submissions else submissions[0]


# options
#   "critique"     "encore"
#   "randomize"    "offset"

def select_near(userid, rating, limit, otherid, folderid, submitid, config=None):
    if config is None:
        config = d.get_config(userid)

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
    query = d.execute(
        "SELECT userid, subtype, settings FROM submission WHERE submitid = %i",
        [submission.submitid], ["single"])

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
    elif submission.subtype / 1000 != query[1] / 1000:
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
    query = d.execute(
        "SELECT userid, subtype, rating FROM submission WHERE submitid = %i",
        [submitid], ["single", "list"])

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
        orm.SubmissionMediaLink.make_or_replace_link(
            submitid, 'cover', cover_media_item, rating=query[2])


@region.cache_on_arguments()
@d.record_timing
def select_recently_popular():
    """
    Get a list of recent, popular submissions. This operation is non-trivial and should
    not be used frequently without caching.

    To calculate scores, this method performs the following evaluation:

    item_score = log(item_fave_count + 1) + log(item_view_counts) / 2 + submission_time / 180000

    180000 is roughly two days. So intuitively an item two days old needs an order of
    magnitude more favorites/views compared to a fresh one. Also the favorites are
    quadratically more influential than views. The result is that this algorithm favors
    recent, heavily favorited items.

    :return: A list of submission dictionaries, in score-rank order.
    """
    max_days = int(d.config_read_setting("popular_max_age_days", "21"))

    query = d.engine.execute("""
        SELECT
            log(count(favorite.*) + 1) +
                log(submission.page_views + 1) / 2 +
                submission.unixtime / 180000 AS score,
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
            LEFT JOIN favorite ON favorite.type = 's' AND submission.submitid = favorite.targetid
        WHERE
            submission.unixtime > EXTRACT(EPOCH FROM now() - %(max_days)s * INTERVAL '1 day')::INTEGER AND
            (favorite.unixtime IS NULL OR favorite.unixtime > EXTRACT(EPOCH FROM now() - %(max_days)s * INTERVAL '1 day')::INTEGER) AND
            submission.settings !~ '[hf]'
        GROUP BY submission.submitid, submission_tags.submitid, profile.userid
        ORDER BY score DESC
        LIMIT 128
    """, max_days=max_days)

    submissions = [dict(row, contype=10) for row in query]
    media.populate_with_submission_media(submissions)
    return submissions

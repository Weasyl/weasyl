from pyramid import httpexceptions
from pyramid.response import Response

from libweasyl.models.content import Submission
from libweasyl.text import markdown_excerpt, slug_for
from weasyl import (
    character, define, journal, macro, media, profile, searchtag, submission)
from weasyl.controllers.decorators import moderator_only
from weasyl.error import WeasylError


def _generate_embed(canonical_path: str, item: dict) -> tuple[dict, dict]:
    """Generate the Twitter and Open Graph embeds for this upload.

    Args:
        canonical_path (str): The canonical path of this upload.
        item (dict): The output of `select_view` for a submission, character, or journal.

    Returns:
        A tuple of two dicts, for use as arguments to `define.webpage`.
        The first dict is `twitter_card`, and the second is `ogp`.
    """
    twitter_meta = {}

    title_with_attribution = f"{item['title']} by {item['username']}"

    # The "og:" prefix is specified in page_start.html, and og:image is required by the OGP spec, so something must be in there.
    ogp = {
        'title': title_with_attribution,
        'type': "website",
        'url': define.absolutify_url(canonical_path),
    }

    if (media_items := item.get('sub_media')) and (cover := media_items.get('cover')):
        twitter_meta['card'] = 'summary_large_image'
        twitter_meta['image'] = ogp['image'] = define.absolutify_url(cover[0]['display_url'])
    elif media_items:
        twitter_meta['card'] = 'summary'
        thumb = media_items.get('thumbnail-custom') or media_items.get('thumbnail-generated')
        if thumb:
            twitter_meta['image'] = ogp['image'] = define.absolutify_url(thumb[0]['display_url'])
        else:
            ogp['image'] = define.get_resource_url('img/logo-mark-light.svg')
    else:
        # Fallback to the user's avatar if there is no image for this upload,
        # such as for journal entries.
        twitter_meta['card'] = 'summary'
        twitter_meta['image'] = ogp['image'] = define.absolutify_url(item['user_media']['avatar'][0]['display_url'])

    if twitter_username := profile.get_twitter_username(item['userid']):
        twitter_meta['creator'] = "@" + twitter_username
        twitter_meta['title'] = item['title']
    else:
        twitter_meta['title'] = title_with_attribution

    meta_description = markdown_excerpt(item['content'])
    if meta_description:
        twitter_meta['description'] = ogp['description'] = meta_description

    return twitter_meta, ogp


def _can_edit_tags(userid: int) -> bool:
    return bool(userid) and define.is_vouched_for(userid)


# Content detail functions
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(request.params.get('submitid'))
    ignore = request.GET.get('ignore') != "false"
    anyway = request.GET.get('anyway') == "true"

    try:
        item = submission.select_view(
            request.userid,
            submitid,
            rating=rating,
            ignore=ignore,
            anyway=anyway,
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Submission", "?ignore=false"),
            ]
        raise

    login = define.get_sysname(item['username'])
    canonical_path = request.route_path('submission_detail_profile', name=login, submitid=submitid, slug=slug_for(item['title']))

    if anyway:
        canonical_path += '?anyway=true'

    if login != username:
        raise httpexceptions.HTTPMovedPermanently(location=canonical_path)

    twitter_meta, ogp = _generate_embed(canonical_path, item)

    return Response(define.webpage(
        request.userid,
        "detail/submission.html",
        (
            request,
            # Myself
            profile.select_myself(request.userid),
            # Submission detail
            item,
            # Subtypes
            macro.MACRO_SUBCAT_LIST,
            # Violations
            [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
        ),
        twitter_card=twitter_meta,
        ogp=ogp,
        canonical_url=canonical_path,
        view_count=True,
        title=item["title"],
        options=("tags-edit",) if _can_edit_tags(request.userid) else (),
    ))


def submission_media_(request):
    link_type = request.matchdict['linktype']
    submitid = int(request.matchdict['submitid'])
    if link_type == "submissions":
        link_type = "submission"

    submission = Submission.query.get(submitid)
    if submission is None:
        raise httpexceptions.HTTPForbidden()
    elif submission.hidden or submission.friends_only:
        raise httpexceptions.HTTPForbidden()
    media_items = media.get_submission_media(submitid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()

    return Response(headerlist=[
        ('X-Accel-Redirect', str(media_items[link_type][0]['file_url']),),
        ('Cache-Control', 'max-age=0',),
    ])


@moderator_only
def submission_tag_history_(request):
    submitid = int(request.matchdict['submitid'])

    page_title = "Tag updates"
    page = define.common_page_start(request.userid, title=page_title)
    page.append(define.render('detail/tag_history.html', [
        submission.select_view_api(
            request.userid,
            submitid,
            # TODO: use mod version of `anyway`; `anyway=True` here only means `ignore=False`
            anyway=True,
            increment_views=False,
        ),
        searchtag.tag_history(submitid),
    ]))
    return Response(define.common_page_end(request.userid, page))


def character_(request):
    rating = define.get_rating(request.userid)
    charid = define.get_int(request.matchdict.get('charid', request.params.get('charid')))
    ignore = request.GET.get('ignore') != "false"
    anyway = request.GET.get('anyway') == "true"

    try:
        item = character.select_view(
            request.userid,
            charid,
            rating=rating,
            ignore=ignore,
            anyway=anyway,
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Character", "?ignore=false"),
            ]
        raise

    canonical_url = "/character/%d/%s" % (charid, slug_for(item["title"]))

    twitter_meta, ogp = _generate_embed(canonical_url, item)

    page = define.common_page_start(
        request.userid,
        canonical_url=canonical_url,
        title=item["title"],
        twitter_card=twitter_meta,
        ogp=ogp,
        view_count=True,
    )
    page.append(define.render('detail/character.html', [
        # Profile
        profile.select_myself(request.userid),
        # Character detail
        item,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    ]))

    return Response(
        define.common_page_end(
            request.userid,
            page,
            options=("tags-edit",) if _can_edit_tags(request.userid) else (),
        )
    )


def journal_(request):
    rating = define.get_rating(request.userid)
    journalid = define.get_int(request.matchdict.get('journalid', request.params.get('journalid')))
    ignore = request.GET.get('ignore') != "false"
    anyway = request.GET.get('anyway') == "true"

    try:
        item = journal.select_view(
            request.userid,
            journalid,
            rating=rating,
            ignore=ignore,
            anyway=anyway,
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Journal", "?ignore=false"),
            ]
        raise

    canonical_url = "/journal/%d/%s" % (journalid, slug_for(item["title"]))

    twitter_meta, ogp = _generate_embed(canonical_url, item)

    page = define.common_page_start(
        request.userid,
        canonical_url=canonical_url,
        title=item["title"],
        twitter_card=twitter_meta,
        ogp=ogp,
        view_count=True,
    )
    page.append(define.render('detail/journal.html', [
        # Myself
        profile.select_myself(request.userid),
        # Journal detail
        item,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 3000 <= i[0] < 4000],
    ]))

    return Response(
        define.common_page_end(
            request.userid,
            page,
            options=("tags-edit",) if _can_edit_tags(request.userid) else (),
        )
    )

from pyramid import httpexceptions
from pyramid.response import Response

from libweasyl.html import strip_html
from libweasyl.models.content import Submission
from libweasyl.text import slug_for
from weasyl import (
    character, define, journal, macro, media, profile, searchtag, submission)
from weasyl.error import WeasylError


# Content detail functions
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(request.params.get('submitid'))
    ignore = request.params.get('ignore', '')
    anyway = request.params.get('anyway', '')

    try:
        item = submission.select_view(
            request.userid, submitid, rating,
            ignore=ignore != 'false', anyway=anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Submission", "?ignore=false"),
                ("Return to the Home Page", "/"),
            ]
        raise

    login = define.get_sysname(item['username'])
    canonical_path = request.route_path('submission_detail_profile', name=login, submitid=submitid, slug=slug_for(item['title']))

    title_with_attribution = f"{item['title']} by {item['username']}"
    twitter_meta = {}

    # The "og:" prefix is specified in page_start.html, and og:image is required by the OGP spec, so something must be in there.
    ogp = {
        'title': title_with_attribution,
        'type': "website",
        'url': define.absolutify_url(canonical_path),
    }

    media_items = item['sub_media']
    cover = media_items.get('cover')
    if cover:
        twitter_meta['card'] = 'summary_large_image'
        twitter_meta['image'] = ogp['image'] = define.absolutify_url(cover[0]['display_url'])
    else:
        twitter_meta['card'] = 'summary'
        thumb = media_items.get('thumbnail-custom') or media_items.get('thumbnail-generated')
        if thumb:
            twitter_meta['image'] = ogp['image'] = define.absolutify_url(thumb[0]['display_url'])
        else:
            ogp['image'] = define.get_resource_url('img/logo-mark-light.svg')

    if twitter_username := profile.get_twitter_username(item['userid']):
        twitter_meta['creator'] = "@" + twitter_username
        twitter_meta['title'] = item['title']
    else:
        twitter_meta['title'] = title_with_attribution

    meta_description = define.summarize(strip_html(item['content']).strip())
    if meta_description:
        twitter_meta['description'] = ogp['description'] = meta_description

    if request.GET.get('anyway'):
        canonical_path += '?anyway=true'

    if login != username:
        raise httpexceptions.HTTPMovedPermanently(location=canonical_path)

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
        title=item["title"],
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


def submission_tag_history_(request):
    submitid = int(request.matchdict['submitid'])

    page_title = "Tag updates"
    page = define.common_page_start(request.userid, title=page_title)
    page.append(define.render('detail/tag_history.html', [
        submission.select_view_api(request.userid, submitid),
        searchtag.tag_history(submitid),
    ]))
    return Response(define.common_page_end(request.userid, page))


def character_(request):
    rating = define.get_rating(request.userid)
    charid = define.get_int(request.matchdict.get('charid', request.params.get('charid')))
    ignore = request.params.get('ignore', '')
    anyway = request.params.get('anyway', '')

    try:
        item = character.select_view(
            request.userid, charid, rating,
            ignore=ignore != 'false', anyway=anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Character", "?ignore=false"),
                ("Return to the Home Page", "/"),
            ]
        raise

    canonical_url = "/character/%d/%s" % (charid, slug_for(item["title"]))

    page = define.common_page_start(request.userid, canonical_url=canonical_url, title=item["title"])
    page.append(define.render('detail/character.html', [
        # Profile
        profile.select_myself(request.userid),
        # Character detail
        item,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    ]))

    return Response(define.common_page_end(request.userid, page))


def journal_(request):
    rating = define.get_rating(request.userid)
    journalid = define.get_int(request.matchdict.get('journalid', request.params.get('journalid')))
    ignore = request.params.get('ignore', '')
    anyway = request.params.get('anyway', '')

    try:
        item = journal.select_view(
            request.userid, rating, journalid,
            ignore=ignore != 'false', anyway=anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Journal", "?ignore=false"),
                ("Return to the Home Page", "/"),
            ]
        raise

    canonical_url = "/journal/%d/%s" % (journalid, slug_for(item["title"]))

    page = define.common_page_start(request.userid, canonical_url=canonical_url, title=item["title"])
    page.append(define.render('detail/journal.html', [
        # Myself
        profile.select_myself(request.userid),
        # Journal detail
        item,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 3000 <= i[0] < 4000],
    ]))

    return Response(define.common_page_end(request.userid, page))

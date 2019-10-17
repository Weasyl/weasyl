

from pyramid import httpexceptions
from pyramid.response import Response

from libweasyl.models.content import Submission
from libweasyl.text import slug_for
from weasyl import (
    character, define, journal, macro, media, profile, searchtag, submission)
from weasyl.error import WeasylError


# Content detail functions
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')

    form = request.web_input(submitid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(form.submitid)

    extras = {}

    if not request.userid:
        # Only generate the Twitter/OGP meta headers if not authenticated (the UA viewing is likely automated).
        twit_card = submission.twitter_card(submitid)
        if define.user_is_twitterbot():
            extras['twitter_card'] = twit_card
        # The "og:" prefix is specified in page_start.html, and og:image is required by the OGP spec, so something must be in there.
        extras['ogp'] = {
            'title': twit_card['title'],
            'site_name': "Weasyl",
            'type': "website",
            'url': twit_card['url'],
            'description': twit_card['description'],
            # >> BUG AVOIDANCE: https://trello.com/c/mBx51jfZ/1285-any-image-link-with-in-it-wont-preview-up-it-wont-show-up-in-embeds-too
            #    Image URLs with '~' in it will not be displayed by Discord, so replace ~ with the URL encoded char code %7E
            'image': twit_card['image:src'].replace('~', '%7E') if 'image:src' in twit_card else define.cdnify_url(
                '/static/images/logo-mark-light.svg'),
        }

    try:
        item = submission.select_view(
            request.userid, submitid, rating,
            ignore=define.text_bool(form.ignore, True), anyway=form.anyway
        )
    except WeasylError as we:
        we.errorpage_kwargs = extras
        if we.value in ("UserIgnored", "TagBlocked"):
            extras['links'] = [
                ("View Submission", "?ignore=false"),
                ("Return to the Home Page", "/index"),
            ]
        raise

    login = define.get_sysname(item['username'])
    canonical_path = request.route_path('submission_detail_profile', name=login, submitid=submitid, slug=slug_for(item['title']))

    if request.GET.get('anyway'):
        canonical_path += '?anyway=true'

    if login != username:
        raise httpexceptions.HTTPMovedPermanently(location=canonical_path)
    extras["canonical_url"] = canonical_path
    extras["title"] = item["title"]

    page = define.common_page_start(request.userid, **extras)
    page.append(define.render('detail/submission.html', [
        # Myself
        profile.select_myself(request.userid),
        # Submission detail
        item,
        # Subtypes
        macro.MACRO_SUBCAT_LIST,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    ]))

    return Response(define.common_page_end(request.userid, page))


def submission_media_(request):
    link_type = request.matchdict['linktype']
    submitid = int(request.matchdict['submitid'])
    if link_type == "submissions":
        link_type = "submission"

    submission = Submission.query.get(submitid)
    if submission is None:
        raise httpexceptions.HTTPForbidden()
    elif submission.is_hidden or submission.is_friends_only:
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
    form = request.web_input(charid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    charid = define.get_int(request.matchdict.get('charid', form.charid))

    try:
        item = character.select_view(
            request.userid, charid, rating,
            ignore=define.text_bool(form.ignore, True), anyway=form.anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Character", "?ignore=false"),
                ("Return to the Home Page", "/index"),
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
    form = request.web_input(journalid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    journalid = define.get_int(request.matchdict.get('journalid', form.journalid))

    try:
        item = journal.select_view(
            request.userid, rating, journalid,
            ignore=define.text_bool(form.ignore, True), anyway=form.anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Journal", "?ignore=false"),
                ("Return to the Home Page", "/index"),
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

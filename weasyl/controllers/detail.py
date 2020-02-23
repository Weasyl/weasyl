from __future__ import absolute_import

from pyramid import httpexceptions
from pyramid.view import view_config
from pyramid.response import Response

from libweasyl.models.content import Submission
from libweasyl.text import slug_for
from weasyl import (
    character, define, journal, macro, media, profile, searchtag, submission)
from weasyl.error import WeasylError


@view_config(route_name="submission_detail_profile;no_s;no_slug", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_profile;no_s", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_profile;no_slug", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_profile", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_view_unnamed", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_view", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail_unnamed", renderer='/detail/submission.jinja2')
@view_config(route_name="submission_detail", renderer='/detail/submission.jinja2')
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')

    form = request.web_input(submitid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(form.submitid)

    extras = {}

    if not request.userid:
        # Only generate the Twitter/OGP meta headers if not authenticated (the UA viewing is likely automated).
        twit_card = submission.twitter_card(request, submitid)
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
            'image': twit_card['image:src'].replace('~', '%7E') if 'image:src' in twit_card else define.get_resource_url(
                'img/logo-mark-light.svg'),
        }

    try:
        item = submission.select_view(
            request.userid, submitid, rating,
            ignore=form.ignore != 'false', anyway=form.anyway
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

    return {
        'title': item["title"],
        # Myself
        'myself': profile.select_myself(request.userid),
        # Submission detail
        'query': item,
        # Subtypes
        'subtypes': dict(macro.MACRO_SUBCAT_LIST),
        # Violations
        'violations': [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    }


@view_config(route_name='submission_detail_media')
def submission_media_(request):
    link_type = request.matchdict['linktype']
    submitid = int(request.matchdict['submitid'])
    if link_type == "submissions":
        link_type = "submission"

    submission = Submission.query.get(submitid)
    if submission is None:
        raise WeasylError('permission')
    elif submission.is_hidden or submission.is_friends_only:
        raise WeasylError('permission')
    media_items = media.get_submission_media(submitid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()

    return Response(headerlist=[
        ('X-Accel-Redirect', str(media_items[link_type][0]['file_url']),),
        ('Cache-Control', 'max-age=0',),
    ])


@view_config(route_name="submission_tag_history", renderer='/detail/tag_history.jinja2')
def submission_tag_history_(request):
    submitid = int(request.matchdict['submitid'])

    return {
        'title': "Tag updates",
        'detail': submission.select_view_api(request.userid, submitid),
        'history': searchtag.tag_history(submitid),
    }


@view_config(route_name="character_detail_unnamed", renderer='/detail/character.jinja2')
@view_config(route_name="character_detail", renderer='/detail/character.jinja2')
def character_(request):
    form = request.web_input(charid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    charid = define.get_int(request.matchdict.get('charid', form.charid))

    try:
        item = character.select_view(
            request.userid, charid, rating,
            ignore=form.ignore != 'false', anyway=form.anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Character", "?ignore=false"),
                ("Return to the Home Page", "/index"),
            ]
        raise

    canonical_url = "/character/%d/%s" % (charid, slug_for(item["title"]))

    return {
        'canonical_url': canonical_url,
        'title': item["title"],
        # Profile
        'myself': profile.select_myself(request.userid),
        # Character detail
        'query': item,
        # Violations
        'violations': [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    }


@view_config(route_name="journal_detail_unnamedited", renderer='/detail/journal.jinja2')
@view_config(route_name="journal_detail", renderer='/detail/journal.jinja2')
def journal_(request):
    form = request.web_input(journalid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    journalid = define.get_int(request.matchdict.get('journalid', form.journalid))

    try:
        item = journal.select_view(
            request.userid, rating, journalid,
            ignore=form.ignore != 'false', anyway=form.anyway
        )
    except WeasylError as we:
        if we.value in ("UserIgnored", "TagBlocked"):
            we.errorpage_kwargs['links'] = [
                ("View Journal", "?ignore=false"),
                ("Return to the Home Page", "/index"),
            ]
        raise

    canonical_url = "/journal/%d/%s" % (journalid, slug_for(item["title"]))

    return {
        'canonical_url': canonical_url,
        'title': item["title"],
        # Myself
        'myself': profile.select_myself(request.userid),
        # Journal detail
        'query': item,
        # Violations
        'violations': [i for i in macro.MACRO_REPORT_VIOLATION if 3000 <= i[0] < 4000],
    }

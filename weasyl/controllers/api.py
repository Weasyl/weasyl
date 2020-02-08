from __future__ import absolute_import

from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.httpexceptions import HTTPUnprocessableEntity
from pyramid.response import Response
from pyramid.view import view_config

from libweasyl.text import markdown, slug_for
from libweasyl import ratings

from weasyl.controllers.decorators import token_checked
from weasyl.error import WeasylError
from weasyl import define as d, macro as m
from weasyl import (
    api, character, collection, commishinfo, favorite, folder,
    index, journal, media, message, profile, submission)


_ERROR_UNEXPECTED = {
    "error": {
        "code": 100,
        "text": "Unexpected"
    }}

_ERROR_UNSIGNED = {
    "error": {
        "code": 110,
        "text": "Session unsigned"
    }}

_ERROR_SITE_STATUS = {
    "error": {
        "code": 115,
        "text": "Site feature temporarily unavailable"
    }}

_ERROR_PERMISSION = {
    "error": {
        "code": 120,
        "text": "Permission denied"
    }}

_CONTENT_IDS = {
    'submissions': 'submitid',
    'characters': 'charid',
    'journals': 'journalid',
}


def api_method(view_callable):
    def wrapper(request):
        try:
            return view_callable(request)
        except WeasylError as e:
            e.render_as_json = True
            raise
        except Exception as e:
            # double underscore here to try to not conflict with any attributes
            # already set on the exception, since we don't know where it's been.
            e.__render_as_json = True
            raise
    return wrapper


_STANDARD_WWW_AUTHENTICATE = 'Bearer realm="Weasyl", Weasyl-API-Key realm="Weasyl"'


# TODO: Additional decorators for things like permissions checks if we ever add moderator/admin endpoints
# that return appropriate json. The common status check should also be refactored to return json.


def api_login_required(view_callable):
    """
    Like decorators.login_required, but returning json on an error.
    """
    # TODO: If we replace the regular @login_required checks on POSTs with a tween, what do about this?
    def inner(request):
        if request.userid == 0:
            raise HTTPUnauthorized(
                json=_ERROR_UNSIGNED,
                www_authenticate=_STANDARD_WWW_AUTHENTICATE,
            )
        return view_callable(request)
    return inner


@view_config(route_name='useravatar', renderer='json')
@api_method
def api_useravatar_(request):
    form = request.web_input(username="")
    userid = profile.resolve_by_login(d.get_sysname(form.username))

    if userid:
        media_items = media.get_user_media(userid)
        return {
            "avatar": d.absolutify_url(media_items['avatar'][0]['display_url']),
        }

    raise WeasylError('userRecordMissing')


@view_config(route_name='whoami', renderer='json')
@api_login_required
def api_whoami_(request):
    return {
        "login": d.get_display_name(request.userid),
        "userid": request.userid,
    }


@view_config(route_name='version', renderer='json')
@api_method
def api_version_(request):
    format = request.matchdict.get("format", ".json")
    if format == '.txt':
        return Response(d.CURRENT_SHA, content_type='text/plain')
    else:
        return {
            "short_sha": d.CURRENT_SHA,
        }


def tidy_submission(submission):
    submission['posted_at'] = d.iso8601(submission.pop('unixtime'))
    submission['sub_media'] = api.tidy_all_media(submission['sub_media'])
    if 'user_media' in submission:
        submission['owner_media'] = api.tidy_all_media(submission.pop('user_media'))
    submission.pop('userid', None)
    subtype = submission.pop('subtype', None)
    if subtype:
        submission['subtype'] = m.CATEGORY_PARSABLE_MAP[subtype // 1000 * 1000]
    contype = submission.pop('contype', None)
    if contype:
        submission['type'] = m.CONTYPE_PARSABLE_MAP[contype]
    submission['rating'] = ratings.CODE_TO_NAME[submission['rating']]
    submission['owner'] = submission.pop('username')
    submission['owner_login'] = d.get_sysname(submission['owner'])
    submission['media'] = submission.pop('sub_media')
    submitid = 0
    if 'submitid' in submission:
        submitid = submission['submitid']
    if 'charid' in submission:
        submitid = submission['charid']
    if submitid > 0:
        if submission['type'] == "usercollect":
            linktype = "submission"
        else:
            linktype = submission['type']
        submission['link'] = d.absolutify_url(
            "/%s/%d/%s" % (linktype, submitid, slug_for(submission['title'])))


@view_config(route_name='api_frontpage', renderer='json')
@api_method
def api_frontpage_(request):
    form = request.web_input(since=None, count=0)
    since = None
    try:
        if form.since:
            since = d.parse_iso8601(form.since)
        count = int(form.count)
    except ValueError:
        raise HTTPUnprocessableEntity(json=_ERROR_UNEXPECTED)
    else:
        count = min(count or 100, 100)

    submissions = index.filter_submissions(request.userid, index.recent_submissions())
    ret = []

    for e, sub in enumerate(submissions, start=1):
        if (since is not None and since >= sub['unixtime']) or (count and e > count):
            break

        tidy_submission(sub)
        ret.append(sub)

    return ret


@view_config(route_name='api_submission_view', renderer='json')
@api_method
def api_submission_view_(request):
    form = request.web_input(anyway='', increment_views='')
    return submission.select_view_api(
        request.userid, int(request.matchdict['submitid']),
        anyway=bool(form.anyway), increment_views=bool(form.increment_views))


@view_config(route_name='api_journal_view', renderer='json')
@api_method
def api_journal_view_(request):
    form = request.web_input(anyway='', increment_views='')
    return journal.select_view_api(
        request.userid, int(request.matchdict['journalid']),
        anyway=bool(form.anyway), increment_views=bool(form.increment_views))


@view_config(route_name='api_character_view', renderer='json')
@api_method
def api_character_view_(request):
    form = request.web_input(anyway='', increment_views='')
    return character.select_view_api(
        request.userid, int(request.matchdict['charid']),
        anyway=bool(form.anyway), increment_views=bool(form.increment_views))


@view_config(route_name='api_user_view', renderer='json')
@api_method
def api_user_view_(request):
    # Helper functions for this view.
    def convert_commission_price(value, options):
        return d.text_price_symbol(options) + d.text_price_amount(value)

    def convert_commission_setting(target):
        if target == "o":
            return "open"
        elif target == "s":
            return "sometimes"
        elif target == "f":
            return "filled"
        elif target == "c":
            return "closed"
        else:
            return None

    userid = request.userid
    otherid = profile.resolve_by_login(d.get_sysname(request.matchdict['login']))
    user = profile.select_profile(otherid)

    rating = d.get_rating(userid)
    o_config = user.pop('config')
    o_settings = user.pop('settings')

    if not otherid and "h" in o_config:
        raise HTTPForbidden(json={
            "error": {
                "code": 200,
                "text": "Profile hidden from unlogged users.",
            },
        })

    user.pop('userid', None)
    user.pop('commish_slots', None)

    user['created_at'] = d.iso8601(user.pop('unixtime'))
    user['media'] = api.tidy_all_media(user.pop('user_media'))
    user['login_name'] = d.get_sysname(user['username'])
    user['profile_text'] = markdown(user['profile_text'])

    folders = folder.select_list(otherid, "api/all")
    if folders:
        old_folders = folders
        folders = list()
        for fldr in (i for i in old_folders if 'parentid' not in i):
            newfolder = {
                "folder_id": fldr['folderid'],
                "title": fldr['title']
            }

            if fldr['haschildren']:
                subfolders = list()
                for sub in (i for i in old_folders if 'parentid' in i and i['parentid'] == fldr['folderid']):
                    subfolders.append({
                        "folder_id": sub['folderid'],
                        "title": sub['title']
                    })

                newfolder['subfolders'] = subfolders

            folders.append(newfolder)

    user['folders'] = folders

    commissions = {
        "details": None,
        "price_classes": None,
        "commissions": convert_commission_setting(o_settings[0]),
        "trades": convert_commission_setting(o_settings[1]),
        "requests": convert_commission_setting(o_settings[2])
    }

    commission_list = commishinfo.select_list(otherid)
    if commission_list:
        commissions['details'] = commission_list['content']

        if len(commission_list['class']) > 0:
            classes = list()
            for cclass in commission_list['class']:
                commission_class = {
                    "title": cclass['title']
                }

                if len(commission_list['price']) > 0:
                    prices = list()
                    for cprice in (i for i in commission_list['price'] if i['classid'] == cclass['classid']):
                        if 'a' in cprice['settings']:
                            ptype = 'additional'
                        else:
                            ptype = 'base'

                        price = {
                            "title": cprice['title'],
                            "price_min": convert_commission_price(cprice['amount_min'], cprice['settings']),
                            "price_max": convert_commission_price(cprice['amount_min'], cprice['settings']),
                            'price_type': ptype
                        }
                        prices.append(price)
                    commission_class['prices'] = prices

                classes.append(commission_class)
            commissions['price_classes'] = classes

    user['commission_info'] = commissions

    user['relationship'] = profile.select_relation(userid, otherid) if userid else None

    if 'O' in o_config:
        submissions = collection.select_list(userid, rating, 11, otherid=otherid)
        more_submissions = 'collections'
        featured = None
    elif 'A' in o_config:
        submissions = character.select_list(userid, rating, 11, otherid=otherid)
        more_submissions = 'characters'
        featured = None
    else:
        submissions = submission.select_list(userid, rating, 11, otherid=otherid, profile_page_filter=True)
        more_submissions = 'submissions'
        featured = submission.select_featured(userid, otherid, rating)

    if submissions:
        for sub in submissions:
            tidy_submission(sub)

    user['recent_submissions'] = submissions
    user['recent_type'] = more_submissions

    if featured:
        tidy_submission(featured)

    user['featured_submission'] = featured

    statistics, show_statistics = profile.select_statistics(otherid)
    if statistics:
        statistics.pop('staff_notes')
    user['statistics'] = statistics if show_statistics else None

    user_info = profile.select_userinfo(otherid)
    if user_info:
        if not user_info['show_age']:
            user_info['age'] = None
        user_info.pop('show_age', None)
        user_info.pop('birthday', None)
        user_info['location'] = user_info.pop('country', None)
    user['user_info'] = user_info
    user['link'] = d.absolutify_url("/~" + user['login_name'])

    return user


@view_config(route_name='api_user_gallery', renderer='json')
@api_method
def api_user_gallery_(request):
    userid = profile.resolve_by_login(d.get_sysname(request.matchdict['login']))
    if not userid:
        raise WeasylError('userRecordMissing')

    form = request.web_input(since=None, count=0, folderid=0, backid=0, nextid=0)
    since = None
    try:
        if form.since:
            since = d.parse_iso8601(form.since)
        count = int(form.count)
        folderid = int(form.folderid)
        backid = int(form.backid)
        nextid = int(form.nextid)
    except ValueError:
        raise HTTPUnprocessableEntity(json=_ERROR_UNEXPECTED)
    else:
        count = min(count or 100, 100)

    submissions = submission.select_list(
        request.userid, d.get_rating(request.userid), count + 1,
        otherid=userid, folderid=folderid, backid=backid, nextid=nextid)
    backid, nextid = d.paginate(submissions, backid, nextid, count, 'submitid')

    ret = []
    for sub in submissions:
        if since is not None and since >= sub['unixtime']:
            break
        tidy_submission(sub)
        ret.append(sub)

    return {
        'backid': backid, 'nextid': nextid,
        'submissions': ret,
    }


@view_config(route_name='api_messages_submissions', renderer='json')
@api_login_required
@api_method
def api_messages_submissions_(request):
    form = request.web_input(count=0, backtime=0, nexttime=0)
    try:
        count = int(form.count)
        backtime = int(form.backtime)
        nexttime = int(form.nexttime)
    except ValueError:
        raise HTTPUnprocessableEntity(json=_ERROR_UNEXPECTED)
    else:
        count = min(count or 100, 100)

    submissions = message.select_submissions(
        request.userid, count + 1, include_tags=True, backtime=backtime, nexttime=nexttime)
    backtime, nexttime = d.paginate(submissions, backtime, nexttime, count, 'unixtime')

    ret = []
    for sub in submissions:
        tidy_submission(sub)
        ret.append(sub)

    return {
        'backtime': backtime, 'nexttime': nexttime,
        'submissions': ret,
    }


@view_config(route_name='api_messages_summary', renderer='json')
@api_login_required
@api_method
def api_messages_summary_(request):
    counts = d._page_header_info(request.userid)
    return {
        'unread_notes': counts[0],
        'comments': counts[1],
        'notifications': counts[2],
        'submissions': counts[3],
        'journals': counts[4],
    }


# TODO(hyena): It's probable that token_checked won't return json from these. Consider writing an api_token_checked.


@view_config(route_name='api_favorite', request_method='POST', renderer='json')
@api_login_required
@api_method
@token_checked
def api_favorite_(request):
    favorite.insert(request.userid,
                    **{_CONTENT_IDS[request.matchdict['content_type']]: int(request.matchdict['content_id'])})

    return {
        'success': True
    }


@view_config(route_name='api_unfavorite', request_method='POST', renderer='json')
@api_login_required
@api_method
@token_checked
def api_unfavorite_(request):
    favorite.remove(request.userid,
                    **{_CONTENT_IDS[request.matchdict['content_type']]: int(request.matchdict['content_id'])})

    return {
        'success': True
    }

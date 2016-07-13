import anyjson as json
import web

from libweasyl.text import markdown, slug_for
from libweasyl import ratings

from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import define as d, macro as m
from weasyl import (
    api, character, collection, commishinfo, favorite, folder,
    index, journal, media, message, profile, searchtag, submission)


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


def api_method(f):
    def wrapper(self, *a, **kw):
        form = web.input(token="")

        if not api.is_api_user() and form.token != d.get_token():
            self.user_id = 0

        web.header('Content-Type', 'application/json')
        try:
            return f(self, *a, **kw)
        except WeasylError as e:
            if web.ctx.status == '200 OK':
                web.ctx.status = '403 Forbidden'
            e.render_as_json = True
            raise
        except Exception as e:
            # double underscore here to try to not conflict with any attributes
            # already set on the exception, since we don't know where it's been.
            e.__render_as_json = True
            raise
    return wrapper


_STANDARD_WWW_AUTHENTICATE = 'Bearer realm="Weasyl", Weasyl-API-Key realm="Weasyl"'


class api_base(controller_base):
    @api_method
    def status_check_fail(self, *args, **kwargs):
        web.ctx.status = '403 Forbidden'
        return json.dumps(_ERROR_SITE_STATUS)

    @api_method
    def permission_check_fail(self, *args, **kwargs):
        web.ctx.status = '403 Forbidden'
        return json.dumps(_ERROR_PERMISSION)

    @api_method
    def login_check_fail(self, *args, **kwargs):
        web.ctx.status = '401 Unauthorized'
        web.header('WWW-Authenticate', _STANDARD_WWW_AUTHENTICATE)
        return json.dumps(_ERROR_UNSIGNED)


class api_useravatar_(api_base):
    def GET(self):
        return self.POST()

    @api_method
    def POST(self):
        # Retrieve form data
        form = web.input(username="")
        userid = profile.resolve_by_login(form.username)

        # Return JSON response
        if userid:
            media_items = media.get_user_media(userid)
            return json.dumps({
                "avatar": d.absolutify_url(media_items['avatar'][0]['display_url']),
            })

        raise WeasylError('userRecordMissing')


class api_searchtagsuggest_(api_base):
    def GET(self):
        return self.POST()

    @api_method
    def POST(self):
        # Retrieve form data
        form = web.input(sid="", target="")

        # Retrieve suggested search tags
        return json.dumps({
            "result": searchtag.suggest(self.user_id, form.target),
        })


class api_whoami_(api_base):
    login_required = True

    @api_method
    def GET(self):
        return json.dumps({
            "login": d.get_display_name(self.user_id),
            "userid": self.user_id,
        })


class api_version_(api_base):
    @api_method
    def GET(self, format='.json'):
        if format == '.txt':
            return d.CURRENT_SHA
        else:
            return json.dumps({
                "short_sha": d.CURRENT_SHA,
            })


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
    return submission


class api_frontpage_(api_base):
    @api_method
    def GET(self):
        form = web.input(since=None, count=0)
        since = None
        try:
            if form.since:
                since = d.parse_iso8601(form.since)
            count = int(form.count)
        except ValueError:
            web.ctx.status = '422 Unprocessable Entity'
            return json.dumps(_ERROR_UNEXPECTED)
        else:
            count = min(count or 100, 100)

        submissions = index.filter_submissions(self.user_id, index.recent_submissions())
        ret = []

        for e, sub in enumerate(submissions, start=1):
            if (since is not None and since >= sub['unixtime']) or (count and e > count):
                break

            tidy_submission(sub)
            ret.append(sub)

        return json.dumps(ret)


class api_submission_view_(api_base):
    @api_method
    def GET(self, submitid):
        form = web.input(anyway='', increment_views='')
        result = submission.select_view_api(
            self.user_id, int(submitid),
            anyway=bool(form.anyway), increment_views=bool(form.increment_views))
        return json.dumps(result)


class api_journal_view_(api_base):
    @api_method
    def GET(self, journalid):
        form = web.input(anyway='', increment_views='')
        result = journal.select_view_api(
            self.user_id, int(journalid),
            anyway=bool(form.anyway), increment_views=bool(form.increment_views))
        return json.dumps(result)


class api_character_view_(api_base):
    @api_method
    def GET(self, charid):
        form = web.input(anyway='', increment_views='')
        result = character.select_view_api(
            self.user_id, int(charid),
            anyway=bool(form.anyway), increment_views=bool(form.increment_views))
        return json.dumps(result)


class api_user_view_(api_base):
    @api_method
    def GET(self, login):
        userid = self.user_id
        otherid = profile.resolve_by_login(login)
        user = profile.select_profile(otherid)

        rating = d.get_rating(userid)
        u_config = d.get_config(userid)
        o_config = user.pop('config')
        o_settings = user.pop('settings')

        if not otherid and "h" in o_config:
            return json.dumps({
                "error": {
                    "code": 200,
                    "text": "Profile hidden from unlogged users."
                }})

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
            "commissions": self.convert_commission_setting(o_settings[0]),
            "trades": self.convert_commission_setting(o_settings[1]),
            "requests": self.convert_commission_setting(o_settings[2])
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
                                "price_min": self.convert_commission_price(cprice['amount_min'], cprice['settings']),
                                "price_max": self.convert_commission_price(cprice['amount_min'], cprice['settings']),
                                'price_type': ptype
                            }
                            prices.append(price)
                        commission_class['prices'] = prices

                    classes.append(commission_class)
                commissions['price_classes'] = classes

        user['commission_info'] = commissions

        user['relationship'] = profile.select_relation(userid, otherid) if userid else None

        if 'O' in o_config:
            submissions = collection.select_list(
                userid, rating, 11, otherid=otherid, options=["cover"], config=u_config)
            more_submissions = 'collections'
            featured = None
        elif 'A' in o_config:
            submissions = character.select_list(
                userid, rating, 11, otherid=otherid, options=["cover"], config=u_config)
            more_submissions = 'characters'
            featured = None
        else:
            submissions = submission.select_list(
                userid, rating, 11, otherid=otherid, options=["cover"], config=u_config,
                profile_page_filter=True)
            more_submissions = 'submissions'
            featured = submission.select_featured(userid, otherid, rating)

        if submissions:
            submissions = map(tidy_submission, submissions)

        user['recent_submissions'] = submissions
        user['recent_type'] = more_submissions

        if featured:
            featured = tidy_submission(featured)

        user['featured_submission'] = featured

        statistics = profile.select_statistics(otherid)
        if statistics:
            statistics.pop('staff_notes')
        user['statistics'] = statistics

        user_info = profile.select_userinfo(otherid)
        if user_info:
            if not user_info['show_age']:
                user_info['age'] = None
            user_info.pop('show_age', None)
            user_info.pop('birthday', None)
            user_info['location'] = user_info.pop('country', None)
        user['user_info'] = user_info
        user['link'] = d.absolutify_url("/~" + user['login_name'])

        return json.dumps(user)

    def convert_commission_price(self, value, options):
        return d.text_price_symbol(options) + d.text_price_amount(value)

    def convert_commission_setting(self, target):
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


class api_user_gallery_(api_base):
    @api_method
    def GET(self, login):
        userid = profile.resolve_by_login(login)
        if not userid:
            web.ctx.status = '404 Not Found'
            raise WeasylError('userRecordMissing')

        form = web.input(since=None, count=0, folderid=0, backid=0, nextid=0)
        since = None
        try:
            if form.since:
                since = d.parse_iso8601(form.since)
            count = int(form.count)
            folderid = int(form.folderid)
            backid = int(form.backid)
            nextid = int(form.nextid)
        except ValueError:
            web.ctx.status = '422 Unprocessable Entity'
            return json.dumps(_ERROR_UNEXPECTED)
        else:
            count = min(count or 100, 100)

        submissions = submission.select_list(
            self.user_id, d.get_rating(self.user_id), count + 1,
            otherid=userid, folderid=folderid, backid=backid, nextid=nextid)
        backid, nextid = d.paginate(submissions, backid, nextid, count, 'submitid')

        ret = []
        for sub in submissions:
            if since is not None and since >= sub['unixtime']:
                break
            tidy_submission(sub)
            ret.append(sub)

        return json.dumps({
            'backid': backid, 'nextid': nextid,
            'submissions': ret,
        })


class api_messages_submissions_(api_base):
    login_required = True

    @api_method
    def GET(self):
        form = web.input(count=0, backtime=0, nexttime=0)
        try:
            count = int(form.count)
            backtime = int(form.backtime)
            nexttime = int(form.nexttime)
        except ValueError:
            web.ctx.status = '422 Unprocessable Entity'
            return json.dumps(_ERROR_UNEXPECTED)
        else:
            count = min(count or 100, 100)

        submissions = message.select_submissions(
            self.user_id, count + 1, backtime=backtime, nexttime=nexttime)
        backtime, nexttime = d.paginate(submissions, backtime, nexttime, count, 'unixtime')

        ret = []
        for sub in submissions:
            tidy_submission(sub)
            ret.append(sub)

        return json.dumps({
            'backtime': backtime, 'nexttime': nexttime,
            'submissions': ret,
        })


class api_messages_summary_(api_base):
    login_required = True

    @api_method
    def GET(self):
        counts = d._page_header_info(self.user_id)
        return json.dumps({
            'unread_notes': counts[0],
            'comments': counts[1],
            'notifications': counts[2],
            'submissions': counts[3],
            'journals': counts[4],
        })


class api_favorite_(api_base):
    login_required = True

    @api_method
    def POST(self, content_type, content_id):
        favorite.insert(self.user_id, **{_CONTENT_IDS[content_type]: int(content_id)})

        return json.dumps({
            'success': True
        })


class api_unfavorite_(api_base):
    login_required = True

    @api_method
    def POST(self, content_type, content_id):
        favorite.remove(self.user_id, **{_CONTENT_IDS[content_type]: int(content_id)})

        return json.dumps({
            'success': True
        })

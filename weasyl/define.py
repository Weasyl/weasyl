from __future__ import absolute_import

import os
import re
import time
import random
import urllib
import hashlib
import hmac
import logging
import numbers
import datetime
import urlparse
import functools
import string
import subprocess
import unicodedata

import anyjson as json
import arrow
from psycopg2cffi.extensions import QuotedString
from pyramid.threadlocal import get_current_request
import pytz
import requests
import sqlalchemy as sa
import sqlalchemy.orm
from web.template import frender

import libweasyl.constants
from libweasyl.legacy import UNIXTIME_OFFSET as _UNIXTIME_OFFSET
from libweasyl.models.tables import metadata as meta
from libweasyl import html, text, ratings, security, staff

from weasyl import config
from weasyl import errorcode
from weasyl import macro
from weasyl.cache import region
from weasyl.compat import FakePyramidRequest
from weasyl.config import config_obj, config_read_setting, config_read_bool
from weasyl.error import WeasylError


_shush_pyflakes = [sqlalchemy.orm]


reload_templates = bool(os.environ.get('WEASYL_RELOAD_TEMPLATES'))
reload_assets = bool(os.environ.get('WEASYL_RELOAD_ASSETS'))


def _load_resources():
    global resource_paths

    with open(os.path.join(macro.MACRO_APP_ROOT, 'build/rev-manifest.json'), 'r') as f:
        resource_paths = json.loads(f.read())


_load_resources()


def record_timing(func):
    key = 'timing.{0.__module__}.{0.__name__}'.format(func)

    @functools.wraps(func)
    def wrapper(*a, **kw):
        start = time.time()
        try:
            return func(*a, **kw)
        finally:
            delta = time.time() - start
            metric('timing', key, delta)

    return wrapper


_sqlalchemy_url = config_obj.get('sqlalchemy', 'url')
if config._in_test:
    _sqlalchemy_url += '_test'
engine = meta.bind = sa.create_engine(_sqlalchemy_url, max_overflow=25, pool_size=10)
sessionmaker = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine, autocommit=True))


def connect():
    """
    Returns the current request's db connection or one from the engine.
    """
    request = get_current_request()
    if request is not None:
        return request.pg_connection
    # If there's no threadlocal request, we're probably operating in a cron task or the like.
    # Return a connection from the pool. n.b. this means that multiple calls could get different
    # connections.
    # TODO(hyena): Does this clean up correctly? There's no registered 'close()' call.
    return sessionmaker()


def log_exc(**kwargs):
    """
    Logs an exception. This is essentially a wrapper around the current request's log_exc.
    It's provided for compatibility for methods that depended on web.ctx.log_exc().
    """
    return get_current_request().log_exc(**kwargs)


def execute(statement, argv=None, options=None):
    """
    Executes an SQL statement; if `statement` represents a SELECT or RETURNING
    statement, the query results will be returned. Note that 'argv' and `options`
    need not be lists if they would have contained only one element.
    """
    db = connect()

    if argv is None:
        argv = list()

    if options is None:
        options = list()

    if argv and not isinstance(argv, list):
        argv = [argv]

    if options and not isinstance(options, list):
        options = [options]

    if argv:
        statement %= tuple([_sql_escape(i) for i in argv])
    query = db.connection().execute(statement)

    if statement.lstrip()[:6] == "SELECT" or " RETURNING " in statement:
        query = query.fetchall()

        if "list" in options or "zero" in options:
            query = [list(i) for i in query]

        if "zero" in options:
            for i in range(len(query)):
                for j in range(len(query[i])):
                    if query[i][j] is None:
                        query[i][j] = 0

        if "bool" in options:
            return query and query[0][0]
        elif "within" in options:
            return [x[0] for x in query]
        elif "single" in options:
            return query[0] if query else list()
        elif "element" in options:
            return query[0][0] if query else list()

        return query
    else:
        query.close()


def _quote_string(s):
    quoted = QuotedString(s).getquoted()
    assert quoted[0] == quoted[-1] == "'"
    return quoted[1:-1].replace('%', '%%')


def _sql_escape(target):
    """
    SQL-escapes `target`; pg_escape_string is used if `target` is a string or
    unicode object, else the integer equivalent is returned.
    """
    if isinstance(target, str):
        # Escape ASCII string
        return _quote_string(target)
    elif isinstance(target, unicode):
        # Escape Unicode string
        return _quote_string(target.encode("utf-8"))
    else:
        # Escape integer
        try:
            return int(target)
        except:
            return 0


def sql_number_list(target):
    """
    Returns a list of numbers suitable for placement after the SQL IN operator in
    a query statement, as in "(1, 2, 3)".
    """
    if not target:
        raise ValueError
    elif not isinstance(target, list):
        target = [target]

    return "(%s)" % (", ".join(["%d" % (i,) for i in target]))


CURRENT_SHA = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip()
the_fake_request = FakePyramidRequest()


# Caching all templates. Parsing templates is slow; we don't need to do it all
# the time and there's plenty of memory for storing the compiled templates.
_template_cache = {}


def _compile(template_name):
    """
    Compiles a template file and returns the result.
    """
    template = _template_cache.get(template_name)

    if template is None or reload_templates:
        template_path = os.path.join(macro.MACRO_APP_ROOT, 'templates', template_name)
        _template_cache[template_name] = template = frender(
            template_path,
            globals={
                "INT": int,
                "STR": str,
                "SUM": sum,
                "LOGIN": get_sysname,
                "TOKEN": get_token,
                "CSRF": _get_csrf_input,
                "USER_TYPE": user_type,
                "DATE": convert_date,
                "TIME": _convert_time,
                "LOCAL_ARROW": local_arrow,
                "PRICE": text_price_amount,
                "SYMBOL": text_price_symbol,
                "TITLE": titlebar,
                "RENDER": render,
                "COMPILE": _compile,
                "CAPTCHA": _captcha_public,
                "MARKDOWN": text.markdown,
                "MARKDOWN_EXCERPT": text.markdown_excerpt,
                "SUMMARIZE": summarize,
                "CONFIG": config_read_setting,
                "SHA": CURRENT_SHA,
                "NOW": get_time,
                "THUMB": thumb_for_sub,
                "M": macro,
                "R": ratings,
                "SLUG": text.slug_for,
                "QUERY_STRING": query_string,
                "INLINE_JSON": html.inline_json,
                "CDNIFY": cdnify_url,
                "PATH": _get_path,
                "arrow": arrow,
                "constants": libweasyl.constants,
                "getattr": getattr,
                "json": json,
                "sorted": sorted,
                "staff": staff,
                "request": the_fake_request,
                "resource_path": get_resource_path,
            })

    return template


def render(template_name, argv=()):
    """
    Renders a template and returns the resulting HTML.
    """
    template = _compile(template_name)
    return unicode(template(*argv))


def titlebar(title, backtext=None, backlink=None):
    return render("common/stage_title.html", [title, backtext, backlink])


def errorpage(userid, code=None, links=None,
              unexpected=None, request_id=None, **extras):
    if links is None:
        links = []

    if code is None:
        code = errorcode.unexpected

        if unexpected:
            code = "".join([code, " The error code associated with this condition "
                                  "is '", unexpected, "'."])
    code = text.markdown(code)

    return webpage(userid, "error/error.html", [code, links, request_id], **extras)


def webpage(userid=0, template=None, argv=None, options=None, **extras):
    if argv is None:
        argv = []

    if options is None:
        options = []

    if template is None:
        if userid:
            template, argv = "error/error.html", [errorcode.signed]
        else:
            template, argv = "error/error.html", [errorcode.unsigned]

    page = common_page_start(userid, options=options, **extras)
    page.append(render(template, argv))

    return common_page_end(userid, page, options=options)


def plaintext(target):
    """
    Returns `target` string stripped of non-ASCII characters.
    """
    return "".join([c for c in target if ord(c) < 128])


def _captcha_section():
    request = get_current_request()
    host = request.environ.get('HTTP_HOST', '').partition(':')[0]
    return 'recaptcha-' + host


def _captcha_public():
    """
    Returns the reCAPTCHA public key, or None if CAPTCHA verification
    is disabled.
    """
    if config_read_bool("captcha_disable_verification", value=False):
        return None

    return config_obj.get(_captcha_section(), 'public_key')


def captcha_verify(captcha_response):
    if config_read_bool("captcha_disable_verification", value=False):
        return True
    if not captcha_response:
        return False

    data = dict(
        secret=config_obj.get(_captcha_section(), 'private_key'),
        response=captcha_response,
        remoteip=get_address())
    response = http_post('https://www.google.com/recaptcha/api/siteverify', data=data)
    captcha_validation_result = response.json()
    return captcha_validation_result['success']


def get_weasyl_session():
    """
    Gets the weasyl_session for the current request. Most code shouldn't have to use this.
    """
    # TODO: This method is inelegant. Remove this logic after updating login.signin().
    return get_current_request().weasyl_session


def get_userid():
    """
    Returns the userid corresponding to the current request, if any.
    """
    return get_current_request().userid


def is_csrf_valid(request, token):
    expected = request.weasyl_session.csrf_token
    return expected is not None and hmac.compare_digest(str(token), str(expected))


def get_token():
    from weasyl import api

    request = get_current_request()

    if api.is_api_user(request):
        return ''

    # allow error pages with $:{TOKEN()} in the template to be rendered even
    # when the error occurred before the session middleware set a session
    if not hasattr(request, 'weasyl_session'):
        return security.generate_key(20)

    sess = request.weasyl_session
    if sess.csrf_token is None:
        sess.csrf_token = security.generate_key(64)
        sess.save = True
    return sess.csrf_token


def _get_csrf_input():
    return '<input type="hidden" name="token" value="%s" />' % (get_token(),)


_SYSNAME_CHARACTERS = (
    set(unicode(string.ascii_lowercase)) |
    set(unicode(string.digits)))


def get_sysname(target):
    """
    Return `target` stripped of all non-alphanumeric characters and lowercased.
    """
    if isinstance(target, unicode):
        normalized = unicodedata.normalize("NFD", target.lower())
        return "".join(i for i in normalized if i in _SYSNAME_CHARACTERS).encode("ascii")
    else:
        return "".join(i for i in target if i.isalnum()).lower()


@region.cache_on_arguments()
@record_timing
def _get_config(userid):
    return engine.scalar("SELECT config FROM profile WHERE userid = %(user)s", user=userid)


def get_config(userid):
    if not userid:
        return ""
    return _get_config(userid)


@region.cache_on_arguments()
@record_timing
def get_login_settings(userid):
    return engine.scalar("SELECT settings FROM login WHERE userid = %(user)s", user=userid)


@region.cache_on_arguments()
@record_timing
def _get_profile_settings(userid):
    """
    This helper function is required because we want to return
    the ProfileSettings object, which by itself is not serializable
    by our cacheing library (or at least, I don't know how to make it so)
    :param userid:
    :return: json representation of profile settings
    """
    if userid is None:
        return {}
    jsonb = engine.scalar("SELECT jsonb_settings FROM profile WHERE userid = %(user)s",
                          user=userid)
    if jsonb is None:
        jsonb = {}
    return jsonb


def get_profile_settings(userid):
    from weasyl.profile import ProfileSettings
    return ProfileSettings(_get_profile_settings(userid))


def get_rating(userid):
    if not userid:
        return ratings.GENERAL.code

    profile_settings = get_profile_settings(userid)

    if is_sfw_mode():
        # if no explicit max SFW rating picked assume general as a safe default
        return profile_settings.max_sfw_rating

    config = get_config(userid)
    if 'p' in config:
        return ratings.EXPLICIT.code
    elif 'a' in config:
        return ratings.MATURE.code
    else:
        return ratings.GENERAL.code


# this method is used specifically for the settings page, where
# the max sfw/nsfw rating need to be displayed separately
def get_config_rating(userid):
    """
    Retrieve the sfw-mode and regular-mode ratings separately
    :param userid: the user to retrieve ratings for
    :return: a tuple of (max_rating, max_sfw_rating)
    """
    config = get_config(userid)

    if 'p' in config:
        max_rating = ratings.EXPLICIT.code
    elif 'a' in config:
        max_rating = ratings.MATURE.code
    else:
        max_rating = ratings.GENERAL.code

    profile_settings = get_profile_settings(userid)
    sfw_rating = profile_settings.max_sfw_rating
    return max_rating, sfw_rating


def is_sfw_mode():
    """
    determine whether the current session is in SFW mode
    :return: TRUE if sfw or FALSE if nsfw
    """
    return get_current_request().cookies.get('sfwmode', "nsfw") == "sfw"


def get_premium(userid):
    if not userid:
        return False

    config = get_config(userid)
    return "d" in config


@region.cache_on_arguments()
@record_timing
def _get_display_name(userid):
    """
    Return the display name assiciated with `userid`; if no such user exists,
    return None.
    """
    return engine.scalar("SELECT username FROM profile WHERE userid = %(user)s", user=userid)


def get_display_name(userid):
    if not userid:
        return None
    return _get_display_name(userid)


def get_int(target):
    if isinstance(target, numbers.Number):
        return int(target)

    try:
        return int("".join(i for i in target if i.isdigit()))
    except:
        return 0


def get_targetid(*argv):
    for i in argv:
        if i:
            return i


def get_search_tag(target):
    target = plaintext(target)
    target = target.replace(" ", "_")
    target = "".join(i for i in target if i.isalnum() or i in "_")
    target = target.strip("_")
    target = "_".join(i for i in target.split("_") if i)

    return target.lower()


def get_time():
    """
    Returns the current unixtime.
    """
    return int(time.time()) + _UNIXTIME_OFFSET


def get_timestamp():
    """
    Returns the current date in the format YYYY-MM.
    """
    return time.strftime("%Y-%m", time.localtime(get_time()))


def _get_hash_path(charid):
    id_hash = hashlib.sha1(str(charid)).hexdigest()
    return "/".join([id_hash[i:i + 2] for i in range(0, 11, 2)]) + "/"


def get_character_directory(charid):
    return macro.MACRO_SYS_CHAR_PATH + _get_hash_path(charid)


def get_userid_list(target):
    query = engine.execute(
        "SELECT userid FROM login WHERE login_name = ANY (%(usernames)s)",
        usernames=[get_sysname(i) for i in target.split(";")])

    return [userid for (userid,) in query]


def get_ownerid(submitid=None, charid=None, journalid=None):
    if submitid:
        return engine.scalar("SELECT userid FROM submission WHERE submitid = %(id)s", id=submitid)
    if charid:
        return engine.scalar("SELECT userid FROM character WHERE charid = %(id)s", id=charid)
    if journalid:
        return engine.scalar("SELECT userid FROM journal WHERE journalid = %(id)s", id=journalid)


def get_random_set(target, count=None):
    """
    Returns the specified number of unique items chosen at random from the target
    list. If more items are specified than the list contains, the full contents
    of the list will be returned in a randomized order.
    """
    if count:
        return random.sample(target, min(count, len(target)))
    else:
        return random.choice(target)


def get_address():
    request = get_current_request()
    return request.client_addr


def _get_path():
    return get_current_request().path_url


def text_price_amount(target):
    return "%.2f" % (float(target) / 100.0)


def text_price_symbol(target):
    from weasyl.commishinfo import CURRENCY_CHARMAP
    for c in target:
        if c in CURRENCY_CHARMAP:
            return CURRENCY_CHARMAP[c].symbol
    return CURRENCY_CHARMAP[''].symbol


def text_first_line(target, strip=False):
    """
    Return the first line of text; if `strip` is True, return all but the first
    line of text.
    """
    first_line, _, rest = target.partition("\n")

    if strip:
        return rest
    else:
        return first_line


def text_fix_url(target):
    if target.startswith(("http://", "https://")):
        return target

    return "http://" + target


def text_bool(target, default=False):
    return target.lower().strip() == "true" or default and target == ""


def local_arrow(dt):
    tz = get_current_request().weasyl_session.timezone
    return arrow.Arrow.fromdatetime(tz.localtime(dt))


def convert_to_localtime(target):
    tz = get_current_request().weasyl_session.timezone
    if isinstance(target, arrow.Arrow):
        return tz.localtime(target.datetime)
    else:
        target = int(get_time() if target is None else target) - _UNIXTIME_OFFSET
        return tz.localtime_from_timestamp(target)


def convert_date(target=None):
    """
    Returns the date in the format 1 January 1970. If no target is passed, the
    current date is returned.
    """
    dt = convert_to_localtime(target)
    result = dt.strftime("%d %B %Y")
    return result[1:] if result and result[0] == "0" else result


def _convert_time(target=None):
    """
    Returns the time in the format 16:00:00. If no target is passed, the
    current time is returned.
    """
    dt = convert_to_localtime(target)
    config = get_config(get_userid())
    if '2' in config:
        return dt.strftime("%I:%M:%S %p %Z")
    else:
        return dt.strftime("%H:%M:%S %Z")


def convert_unixdate(day, month, year, escape=True):
    """
    Returns the unixtime corresponding to the beginning of the specified date; if
    the date is not valid, None is returned.
    """
    if escape:
        day, month, year = (get_int(i) for i in [day, month, year])

    try:
        ret = int(time.mktime(datetime.date(year, month, day).timetuple()))
    except:
        return
    # range of a postgres integer
    if ret > 2147483647 or ret < -2147483648:
        return None
    return ret


def convert_inputdate(target):
    def _month(target):
        target = "".join(i for i in target if i in "abcdefghijklmnopqrstuvwxyz")
        for i, j in enumerate(["ja", "f", "mar", "ap", "may", "jun", "jul", "au",
                               "s", "o", "n", "d"]):
            if target.startswith(j):
                return i + 1

    target = target.strip().lower()

    if not target:
        return

    if re.match(r"[0-9]+ [a-z]+,? [0-9]+", target):
        # 1 January 1990
        target = target.split()
        target[0] = get_int(target[0])
        target[2] = get_int(target[2])

        if 1933 <= target[0] <= 2037:
            return convert_unixdate(target[2], _month(target[1]), target[0])
        else:
            return convert_unixdate(target[0], _month(target[1]), target[2])
    elif re.match("[a-z]+ [0-9]+,? [0-9]+", target):
        # January 1 1990
        target = target.split()
        target[1] = get_int(target[1])
        target[2] = get_int(target[2])

        return convert_unixdate(target[1], _month(target[0]), target[2])
    elif re.match("[0-9]+ ?/ ?[0-9]+ ?/ ?[0-9]+", target):
        # 1/1/1990
        target = target.split("/")
        target[0] = get_int(target[0])
        target[1] = get_int(target[1])
        target[2] = get_int(target[2])

        if target[0] > 12:
            return convert_unixdate(target[0], target[1], target[2])
        else:
            return convert_unixdate(target[1], target[0], target[2])


def convert_age(target):
    return (get_time() - target) / 31556926


def age_in_years(birthdate):
    """
    Determines an age in years based off of the given arrow.Arrow birthdate
    and the current date.
    """
    now = arrow.now()
    is_upcoming = (now.month, now.day) < (birthdate.month, birthdate.day)

    return now.year - birthdate.year - int(is_upcoming)


def user_type(userid):
    if userid in staff.DIRECTORS:
        return "director"
    if userid in staff.TECHNICAL:
        return "tech"
    if userid in staff.ADMINS:
        return "admin"
    if userid in staff.MODS:
        return "mod"
    if userid in staff.DEVELOPERS:
        return "dev"

    return None


@region.cache_on_arguments(expiration_time=180)
@record_timing
def _page_header_info(userid):
    messages = engine.scalar(
        "SELECT COUNT(*) FROM message WHERE otherid = %(user)s AND settings ~ 'u'", user=userid)
    result = [messages, 0, 0, 0, 0]

    counts = engine.execute(
        """
        SELECT type / 1000 AS group, COUNT(*) AS count
        FROM welcome
            LEFT JOIN submission
                ON welcome.targetid = submission.submitid
                AND welcome.type BETWEEN 2000 AND 2999
        WHERE
            welcome.userid = %(user)s
            AND (
                submission.rating IS NULL
                OR submission.rating <= %(rating)s
            )
        GROUP BY "group"
        """, user=userid, rating=get_rating(userid))

    for group, count in counts:
        result[5 - group] = count

    return result


def page_header_info(userid):
    from weasyl import media
    sfw = get_current_request().cookies.get('sfwmode', 'nsfw')
    return {
        "welcome": _page_header_info(userid),
        "userid": userid,
        "username": get_display_name(userid),
        "user_media": media.get_user_media(userid),
        "sfw": sfw,
    }


def common_page_start(userid, options=None, **extended_options):
    if options is None:
        options = []

    userdata = None
    if userid:
        userdata = page_header_info(userid)

    data = render(
        "common/page_start.html", [userdata, options, extended_options])

    return [data]


def _active_users(seconds):
    usercount_url_template = config_read_setting('url_template', section='usercount')
    if not usercount_url_template:
        return
    try:
        resp = http_get(usercount_url_template % (seconds,))
    except WeasylError:
        return
    if resp.status_code != 200:
        return
    return resp.json()['users']


@region.cache_on_arguments(expiration_time=600)
@record_timing
def active_users():
    active_users = []
    for span, seconds in [('hour', 60 * 60), ('day', 60 * 60 * 24)]:
        users = _active_users(seconds)
        if users:
            active_users.append((span, users))

    return '; '.join(
        '%d users active in the last %s' % (users, span)
        for span, users in active_users)


def common_page_end(userid, page, options=None):
    active_users_string = active_users()
    data = render("common/page_end.html", (options, active_users_string))
    page.append(data)
    return "".join(page)


def common_status_check(userid):
    """
    Returns the name of the script to which the user should be redirected
    if required.
    """
    if not userid:
        return None

    settings = get_login_settings(userid)

    if "p" in settings:
        return "resetpassword"
    if "i" in settings:
        return "resetbirthday"
    if "e" in settings:
        return "resetemail"
    if "b" in settings:
        return "banned"
    if "s" in settings:
        return "suspended"

    return None


def common_status_page(userid, status):
    """
    Raise the redirect to the script returned by common_status_check() or render
    the appropriate site status error page.
    """
    if status == "admin":
        return errorpage(0, errorcode.admin_mode)
    elif status == "local":
        return errorpage(0, errorcode.local_mode)
    elif status == "offline":
        return errorpage(0, errorcode.offline_mode)
    elif status == "address":
        return "IP ADDRESS TEMPORARILY REJECTED"
    elif status == "resetpassword":
        return webpage(userid, "force/resetpassword.html")
    elif status == "resetbirthday":
        return webpage(userid, "force/resetbirthday.html")
    elif status == "resetemail":
        return "reset email"  # todo
    elif status in ('banned', 'suspended'):
        from weasyl import moderation, login

        login.signout(get_current_request())
        if status == 'banned':
            reason = moderation.get_ban_reason(userid)
            return errorpage(
                userid,
                "Your account has been permanently banned and you are no longer allowed "
                "to sign in.\n\n%s\n\nIf you believe this ban is in error, please "
                "contact support@weasyl.com for assistance." % (reason,))

        elif status == 'suspended':
            suspension = moderation.get_suspension(userid)
            return errorpage(
                userid,
                "Your account has been temporarily suspended and you are not allowed to "
                "be logged in at this time.\n\n%s\n\nThis suspension will be lifted on "
                "%s.\n\nIf you believe this suspension is in error, please contact "
                "support@weasyl.com for assistance." % (suspension.reason, convert_date(suspension.release)))


_content_types = {
    'submit': 110,
    'char': 120,
    'journal': 130,
    'profile': 210,
}


def common_view_content(userid, targetid, feature):
    """
    Return True if a record was successfully inserted into the views table
    and the page view statistic incremented, else False.
    """
    if feature == "profile" and targetid == userid:
        return

    typeid = _content_types.get(feature, 0)
    if userid:
        viewer = 'user:%d' % (userid,)
    else:
        viewer = get_address()

    result = engine.execute(
        'INSERT INTO views (viewer, targetid, type) VALUES (%(viewer)s, %(targetid)s, %(type)s) ON CONFLICT DO NOTHING',
        viewer=viewer, targetid=targetid, type=typeid)

    if result.rowcount == 0:
        return False

    if feature == "submit":
        engine.execute("UPDATE submission SET page_views = page_views + 1 WHERE submitid = %(id)s", id=targetid)
    elif feature == "char":
        engine.execute("UPDATE character SET page_views = page_views + 1 WHERE charid = %(id)s", id=targetid)
    elif feature == "journal":
        engine.execute("UPDATE journal SET page_views = page_views + 1 WHERE journalid = %(id)s", id=targetid)
    elif feature == "profile":
        engine.execute("UPDATE profile SET page_views = page_views + 1 WHERE userid = %(id)s", id=targetid)

    return True


def append_to_log(logname, **parameters):
    parameters['when'] = datetime.datetime.now().isoformat()
    log_path = '%s%s.%s.log' % (macro.MACRO_SYS_LOG_PATH, logname, get_timestamp())
    with open(log_path, 'a') as outfile:
        outfile.write(json.dumps(parameters))
        outfile.write('\n')


_CHARACTER_SETTINGS_FEATURE_SYMBOLS = {
    "char/thumb": "-",
    "char/cover": "~",
    "char/submit": "=",
}

_CHARACTER_SETTINGS_TYPE_EXTENSIONS = {
    "J": ".jpg",
    "P": ".png",
    "G": ".gif",
    "T": ".txt",
    "H": ".htm",
    "M": ".mp3",
    "F": ".swf",
    "A": ".pdf",
}


def url_type(settings, feature):
    """
    Return the file extension specified in `settings` for the passed feature.
    """
    symbol = _CHARACTER_SETTINGS_FEATURE_SYMBOLS[feature]
    type_code = settings[settings.index(symbol) + 1]

    return _CHARACTER_SETTINGS_TYPE_EXTENSIONS[type_code]


def url_make(targetid, feature, query=None, root=False, file_prefix=None):
    """
    Return the URL to a resource; if `root` is True, the path will start from
    the root.
    """
    result = [] if root else ["/"]

    if root:
        result.append(macro.MACRO_STORAGE_ROOT)

    if "char/" in feature:
        result.extend([macro.MACRO_URL_CHAR_PATH, _get_hash_path(targetid)])

    if file_prefix is not None:
        result.append("%s-" % (file_prefix,))

    # Character file
    if feature == "char/submit":
        if query is None:
            query = engine.execute("SELECT userid, settings FROM character WHERE charid = %(id)s", id=targetid).first()

        if query and "=" in query[1]:
            result.append("%i.submit.%i%s" % (targetid, query[0], url_type(query[1], feature)))
        else:
            return None
    # Character cover
    elif feature == "char/cover":
        if query is None:
            query = engine.execute("SELECT settings FROM character WHERE charid = %(id)s", id=targetid).first()

        if query and "~" in query[0]:
            result.append("%i.cover%s" % (targetid, url_type(query[0], feature)))
        else:
            return None
    # Character thumbnail
    elif feature == "char/thumb":
        if query is None:
            query = engine.execute("SELECT settings FROM character WHERE charid = %(id)s", id=targetid).first()

        if query and "-" in query[0]:
            result.append("%i.thumb%s" % (targetid, url_type(query[0], feature)))
        else:
            return None if root else macro.MACRO_BLANK_THUMB
    # Character thumbnail selection
    elif feature == "char/.thumb":
        result.append("%i.new.thumb" % (targetid,))

    return "".join(result)


def cdnify_url(url):
    cdn_root = config_read_setting("cdn_root")
    if not cdn_root:
        return url

    return urlparse.urljoin(cdn_root, url)


def get_resource_path(resource):
    if reload_assets:
        _load_resources()

    return '/' + resource_paths[resource]


def absolutify_url(url):
    cdn_root = config_read_setting("cdn_root")
    if cdn_root and url.startswith(cdn_root):
        return url

    return urlparse.urljoin(get_current_request().application_url, url)


def user_is_twitterbot():
    return get_current_request().environ.get('HTTP_USER_AGENT', '').startswith('Twitterbot')


def summarize(s, max_length=200):
    if len(s) > max_length:
        return s[:max_length - 1].rstrip() + u'\N{HORIZONTAL ELLIPSIS}'
    return s


def clamp(val, lower_bound, upper_bound):
    return min(max(val, lower_bound), upper_bound)


def timezones():
    ct = datetime.datetime.now(pytz.utc)
    timezones_by_country = [
        (pytz.country_names[cc], [
            (int(ct.astimezone(pytz.timezone(tzname)).strftime("%z")), tzname)
            for tzname in timezones
        ])
        for cc, timezones in pytz.country_timezones.iteritems()]
    timezones_by_country.sort()
    ret = []
    for country, timezones in timezones_by_country:
        ret.append(('- %s -' % (country,), None))
        ret.extend(
            ("[UTC%+05d] %s" % (offset, tzname.replace('_', ' ')), tzname)
            for offset, tzname in timezones)
    return ret


def query_string(query):
    pairs = []

    for key, value in query.items():
        if isinstance(value, (tuple, list, set)):
            for subvalue in value:
                if isinstance(subvalue, unicode):
                    pairs.append((key, subvalue.encode("utf-8")))
                else:
                    pairs.append((key, subvalue))
        elif isinstance(value, unicode):
            pairs.append((key, value.encode("utf-8")))
        elif value:
            pairs.append((key, value))

    return urllib.urlencode(pairs)


def _requests_wrapper(func_name):
    func = getattr(requests, func_name)

    def wrapper(*a, **kw):
        request = get_current_request()
        try:
            return func(*a, **kw)
        except Exception as e:
            request.log_exc(level=logging.DEBUG)
            w = WeasylError('httpError')
            w.error_suffix = 'The original error was: %s' % (e,)
            raise w

    return wrapper


http_get = _requests_wrapper('get')
http_post = _requests_wrapper('post')

# This will be set by twisted.
statsFactory = None


def metric(*a, **kw):
    statsFactory.metric(*a, **kw)


def iso8601(unixtime):
    if isinstance(unixtime, arrow.Arrow):
        return unixtime.isoformat().partition('.')[0] + 'Z'
    else:
        return datetime.datetime.utcfromtimestamp(unixtime - _UNIXTIME_OFFSET).isoformat() + 'Z'


def parse_iso8601(s):
    return arrow.Arrow.strptime(s, '%Y-%m-%dT%H:%M:%SZ').timestamp + _UNIXTIME_OFFSET


def paginate(results, backid, nextid, limit, key):
    at_start = at_end = False
    # if neither value is specified, we're definitely at the start
    if not backid and not nextid:
        at_start = True

    # if we were cut short...
    if len(results) <= limit:
        if backid:
            # if moving backward we're at the start
            at_start = True
        else:
            # if moving forward we're at the end
            at_end = True
    elif backid:
        # delete extraneous rows from the front if we're moving backward
        del results[:-limit]
    else:
        # or from the back if we're moving forward
        del results[limit:]

    return (
        None if at_start or not results else results[0][key],
        None if at_end or not results else results[-1][key])


def thumb_for_sub(submission):
    """
    Given a submission dict containing sub_media, sub_type and userid,
    returns the appropriate media item to use as a thumbnail.

    Params:
        submission: The submission.

    Returns:
        The sub media to use as a thumb.
    """
    user_id = get_userid()
    profile_settings = get_profile_settings(user_id)
    if (profile_settings.disable_custom_thumbs and
            submission.get('subtype', 9999) < 2000 and
            submission['userid'] != user_id):
        thumb_key = 'thumbnail-generated'
    else:
        thumb_key = 'thumbnail-custom' if 'thumbnail-custom' in submission['sub_media'] else 'thumbnail-generated'

    return submission['sub_media'][thumb_key][0]

# define.py

import re
import time
import random
import urllib
import hashlib
import logging
import numbers
import datetime
import urlparse
import functools
import traceback
import string
import subprocess
import unicodedata

import anyjson as json
import arrow
import requests
import web
import sqlalchemy as sa
import sqlalchemy.orm
from psycopg2.extensions import QuotedString
import pytz

import macro
import errorcode
from error import WeasylError

from libweasyl.legacy import UNIXTIME_OFFSET as _UNIXTIME_OFFSET
from libweasyl.models.tables import metadata as meta
from libweasyl import html, text, ratings, security, staff

from weasyl.compat import FakePyramidRequest
from weasyl.config import config_obj, config_read, config_read_setting, config_read_bool
from weasyl.cache import region
from weasyl import config


_shush_pyflakes = [sqlalchemy.orm, config_read]


# XXX: eventually figure out how to include this in libweasyl.
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
    if 'pg_connection' not in web.ctx:
        web.ctx.pg_connection = db = sessionmaker()
        try:
            # Make sure postgres is still there before issuing any further queries.
            db.execute('SELECT 1')
        except sa.exc.OperationalError:
            log_exc = web.ctx.env.get('raven.captureException', traceback.print_exc)
            log_exc()
            raise web.webapi.HTTPError('503 Service Unavailable', data='database error')
    return web.ctx.pg_connection


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
        statement %= tuple([sql_escape(i) for i in argv])
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


def quote_string(s):
    """
    SQL-escapes `target`; pg_escape_string is used if `target` is a string or
    unicode object, else the integer equivalent is returned.
    """
    quoted = QuotedString(s).getquoted()
    assert quoted[0] == quoted[-1] == "'"
    return quoted[1:-1].replace('%', '%%')


def sql_escape(target):
    if isinstance(target, str):
        # Escape ASCII string
        return quote_string(target)
    elif isinstance(target, unicode):
        # Escape Unicode string
        return quote_string(target.encode("utf-8"))
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

    return "(%s)" % (", ".join([str(i) for i in target]))


def sql_number_series(target):
    """
    Returns a list of numbers suitable for placement after the SQL VALUES
    operator in a query statement, as in "(1, 2), (3, 4), (5, 6)".
    """
    if not target:
        raise ValueError

    return ", ".join(sql_number_list(i) for i in target)


def sql_string_list(target, exception=True):
    """
    Returns a list of strings suitable for placement after the SQL IN operator in
    a query statement, as in "('foo', 'bar', 'baz')".
    """
    if not target:
        raise ValueError
    elif not isinstance(target, list):
        target = [target]

    return "(%s)" % (", ".join(["'%s'" % (sql_escape(i)) for i in target]))


def sql_string_series(target):
    if not target:
        raise ValueError

    return ", ".join(sql_string_list(i) for i in target)


CURRENT_SHA = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip()
the_fake_request = FakePyramidRequest()


# Renders a template file and returns the result.

# Caching all templates. Parsing templates is slow; we don't need to do it all
# the time and there's plenty of memory for storing the compiled templates.
_template_cache = {}


def render(template_name, argv=(), cached=False):
    if isinstance(template_name, basestring):
        template = _template_cache.get(template_name)
    else:
        template = template_name
    if template is None:
        _template_cache[template_name] = template = web.template.frender(
            "%stemplates/%s" % (macro.MACRO_SYS_BASE_PATH, template_name),
            globals={
                "INT": int,
                "STR": str,
                "SUM": sum,
                "LOGIN": get_sysname,
                "TOKEN": get_token,
                "CSRF": get_csrf_token,
                "USER_TYPE": user_type,
                "DATE": convert_date,
                "TIME": convert_time,
                "PRICE": text_price_amount,
                "SYMBOL": text_price_symbol,
                "TITLE": titlebar,
                "RENDER": render,
                "COMPILE": compile,
                "CAPTCHA": captcha_public,
                "MARKDOWN": text.markdown,
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
                "PATH": get_path,
                "arrow": arrow,
                "getattr": getattr,
                "sorted": sorted,
                "staff": staff,
                "request": the_fake_request,
            })

    if argv is None:
        return template
    else:
        return unicode(template(*argv))


def compile(target):
    """
    Compiles a template file and returns the result.
    """
    return render(target, None)


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
    host = web.ctx.env.get('HTTP_HOST', '').partition(':')[0]
    return 'recaptcha-' + host


def captcha_public():
    """
    Returns the reCAPTCHA public key, or None if CAPTCHA verification
    is disabled.
    """
    if config_read_bool("captcha_disable_verification", value=False):
        return None

    return config_obj.get(_captcha_section(), 'public_key')


def captcha_verify(form):
    if config_read_bool("captcha_disable_verification", value=False):
        return True
    if not form.g_recaptcha_response:
        return False

    data = dict(
        secret=config_obj.get(_captcha_section(), 'private_key'),
        remoteip=get_address(),
        response=form.g_recaptcha_response)

    response = http_post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = response.text.splitlines()
    return result[0] == 'true'


def get_userid(sessionid=None):
    """
    Returns the userid corresponding to the user's sessionid; if no such session
    exists, zero is returned.
    """
    api_token = web.ctx.env.get('HTTP_X_WEASYL_API_KEY')
    authorization = web.ctx.env.get('HTTP_AUTHORIZATION')
    if api_token is not None:
        userid = engine.execute("SELECT userid FROM api_tokens WHERE token = %(token)s", token=api_token).scalar()
        if not userid:
            web.header('WWW-Authenticate', 'Weasyl-API-Key realm="Weasyl"')
            raise web.webapi.Unauthorized()
        return userid

    elif authorization:
        from weasyl.oauth2 import get_userid_from_authorization
        userid = get_userid_from_authorization()
        if not userid:
            web.header('WWW-Authenticate', 'Bearer realm="Weasyl" error="invalid_token"')
            raise web.webapi.Unauthorized()
        return userid

    else:
        userid = web.ctx.weasyl_session.userid
        return 0 if userid is None else userid


def get_token():
    import api

    if api.is_api_user():
        return ''

    sess = web.ctx.weasyl_session
    if sess.csrf_token is None:
        sess.csrf_token = security.generate_key(64)
        sess.save = True
    return sess.csrf_token


def get_csrf_token():
    return '<input type="hidden" name="token" value="%s" />' % (get_token(),)


SYSNAME_CHARACTERS = (
    set(unicode(string.ascii_lowercase)) |
    set(unicode(string.digits)))


def get_sysname(target):
    """
    Return `target` stripped of all non-alphanumeric characters and lowercased.
    """
    if isinstance(target, unicode):
        normalized = unicodedata.normalize("NFD", target.lower())
        return "".join(i for i in normalized if i in SYSNAME_CHARACTERS).encode("ascii")
    else:
        return "".join(i for i in target if i.isalnum()).lower()


@region.cache_on_arguments()
@record_timing
def _get_config(userid):
    return engine.execute("SELECT config FROM profile WHERE userid = %(user)s", user=userid).scalar()


def get_config(userid):
    if not userid:
        return ""
    return _get_config(userid)


@region.cache_on_arguments()
@record_timing
def get_login_settings(userid):
    return engine.execute("SELECT settings FROM login WHERE userid = %(user)s", user=userid).scalar()


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
    jsonb = engine.execute("SELECT jsonb_settings FROM profile WHERE userid = %(user)s",
                           user=userid).scalar()
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
    elif 'm' in config:
        return ratings.MODERATE.code
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

    max_rating = ratings.GENERAL.code
    if 'p' in config:
        max_rating = ratings.EXPLICIT.code
    elif 'a' in config:
        max_rating = ratings.MATURE.code
    elif 'm' in config:
        max_rating = ratings.MODERATE.code

    profile_settings = get_profile_settings(userid)
    sfw_rating = profile_settings.max_sfw_rating
    return max_rating, sfw_rating


def is_sfw_mode():
    """
    determine whether the current session is in SFW mode
    :return: TRUE if sfw or FALSE if nsfw
    """
    return web.cookies(sfwmode="nsfw").sfwmode == "sfw"


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
    return engine.execute("SELECT username FROM profile WHERE userid = %(user)s", user=userid).scalar()


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


_hash_path_roots = {
    "user": [macro.MACRO_SYS_USER_PATH],
    "save": [macro.MACRO_SYS_SAVE_PATH],
    "submit": [macro.MACRO_SYS_SUBMIT_PATH],
    "char": [macro.MACRO_SYS_CHAR_PATH],
    "journal": [macro.MACRO_SYS_JOURNAL_PATH],
    None: [],
}


def get_hash_path(target_id, content_type=None):
    path_hash = hashlib.sha1(str(target_id)).hexdigest()
    path_hash = "/".join([path_hash[i:i + 2] for i in range(0, 11, 2)])

    root = _hash_path_roots[content_type]

    return "".join(root + [path_hash, "/"])


def get_userid_list(target):
    query = engine.execute(
        "SELECT userid FROM login WHERE login_name = ANY (%(usernames)s)",
        usernames=[get_sysname(i) for i in target.split(";")])

    return [userid for (userid,) in query]


def get_ownerid(submitid=None, charid=None, journalid=None, commishid=None):
    if submitid:
        return engine.execute("SELECT userid FROM submission WHERE submitid = %(id)s", id=submitid).scalar()
    if charid:
        return engine.execute("SELECT userid FROM character WHERE charid = %(id)s", id=charid).scalar()
    if journalid:
        return engine.execute("SELECT userid FROM journal WHERE journalid = %(id)s", id=journalid).scalar()
    if commishid:
        return engine.execute("SELECT userid FROM commission WHERE commishid = %(id)s", id=commishid).scalar()


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
    return web.ctx.env.get("HTTP_X_FORWARDED_FOR", web.ctx.ip)


def get_path():
    return web.ctx.homepath + web.ctx.fullpath


def text_price_amount(target):
    return "%i.%s%i" % (target / 100, "" if target % 100 > 9 else "0", target % 100)


def text_price_symbol(target):
    if "e" in target:
        return "&#8364;"
    elif "p" in target:
        return "&#163;"
    elif "y" in target:
        return "&#165;"
    elif "c" in target:
        return "C&#36;"
    elif "u" in target:
        return "A&#36;"
    elif "m" in target:
        return "M&#36;"
    else:
        return "&#36;"


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


def convert_to_localtime(target):
    tz = web.ctx.weasyl_session.timezone
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


def convert_time(target=None):
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
    messages = engine.execute(
        "SELECT COUNT(*) FROM message WHERE otherid = %(user)s AND settings ~ 'u'", user=userid).scalar()
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
    sfw = web.cookies(sfwmode="nsfw").sfwmode
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


def common_page_end(userid, page, rating=None, config=None,
                    now=None, options=None):
    active_users_string = active_users()
    data = render("common/page_end.html", [options, active_users_string])
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

        login.signout(userid)
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
    Return True if a record was successfully inserted into the contentview table
    and the page view statistic incremented, else False.
    """
    if feature == "profile" and targetid == userid:
        return

    typeid = _content_types.get(feature, 0)
    if userid:
        viewer = 'user:%d' % (userid,)
    else:
        viewer = get_address()

    try:
        engine.execute(
            meta.tables['views'].insert()
            .values(viewer=viewer, targetid=targetid, type=typeid))
    except sa.exc.IntegrityError:
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
        result.append(macro.MACRO_SYS_BASE_PATH)

    if "char/" in feature:
        result.extend([macro.MACRO_URL_CHAR_PATH, get_hash_path(targetid)])

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


def absolutify_url(url):
    cdn_root = config_read_setting("cdn_root")
    if cdn_root and url.startswith(cdn_root):
        return url

    return urlparse.urljoin(web.ctx.realhome, url)


def user_is_twitterbot():
    return web.ctx.env.get('HTTP_USER_AGENT', '').startswith('Twitterbot')


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
        try:
            return func(*a, **kw)
        except Exception as e:
            web.ctx.log_exc(level=logging.DEBUG)
            w = WeasylError('httpError')
            w.error_suffix = 'The original error was: %s' % (e,)
            raise w

    return wrapper

http_get = _requests_wrapper('get')
http_post = _requests_wrapper('post')


def metric(*a, **kw):
    from weasyl.wsgi import app
    app.statsFactory.metric(*a, **kw)


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


def token_checked(handler):
    from weasyl import api

    def wrapper(self, *args, **kwargs):
        form = web.input(token="")

        if not api.is_api_user() and form.token != get_token():
            return errorpage(self.user_id, errorcode.token)

        return handler(self, *args, **kwargs)

    return wrapper


def supports_json(handler):
    def wrapper(*args, **kwargs):
        form = web.input(format="")

        if form.format == "json":
            web.header("Content-Type", "application/json")

            try:
                result = handler(*args, **kwargs)
            except WeasylError as e:
                result = {"error": e.value, "message": errorcode.error_messages.get(e.value)}

            return json.dumps(result)

        return handler(*args, **kwargs)

    return wrapper


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

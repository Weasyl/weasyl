import os
import time
import hashlib
import itertools
import json
import numbers
import datetime
import pkgutil
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode, urljoin

import arrow
from pyramid.threadlocal import get_current_request
import requests
import sqlalchemy as sa
import sqlalchemy.orm
from pyramid.response import Response
from sqlalchemy.exc import OperationalError
from web.template import Template

import libweasyl.constants
from libweasyl.cache import region
from libweasyl.legacy import UNIXTIME_OFFSET as _UNIXTIME_OFFSET, get_sysname
from libweasyl.models.tables import metadata as meta
from libweasyl import html, text, ratings, staff

from weasyl import config
from weasyl import errorcode
from weasyl import macro
from weasyl.config import config_obj, config_read_setting
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
    return func


_sqlalchemy_url = config_obj.get('sqlalchemy', 'url')
if config._in_test:
    _sqlalchemy_url += '_test'
engine = meta.bind = sa.create_engine(
    _sqlalchemy_url,
    pool_use_lifo=True,
    pool_size=2,
    connect_args={
        'options': '-c TimeZone=UTC',
    },
)
sessionmaker_future = sa.orm.sessionmaker(bind=engine, expire_on_commit=False)
sessionmaker = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine, autocommit=True))


def connect():
    """
    Returns the current request's db connection or one from the engine.
    """
    request = get_current_request()
    if request is not None:
        return request.pg_connection
    # If there's no threadlocal request, this could be… a manual query?
    # Return a connection from the pool. n.b. this means that multiple calls could get different
    # connections.
    # TODO(hyena): Does this clean up correctly? There's no registered 'close()' call.
    return sessionmaker()


def execute(statement, argv=None):
    """
    Executes an SQL statement; if `statement` represents a SELECT or RETURNING
    statement, the query results will be returned.
    """
    db = connect()

    if argv:
        argv = tuple(argv)

        for x in argv:
            if type(x) is not int:
                raise TypeError("can't use %r as define.execute() parameter" % (x,))

        statement %= argv

    query = db.connection().execute(statement)

    if statement.lstrip()[:6] == "SELECT" or " RETURNING " in statement:
        return query.fetchall()
    else:
        query.close()


def column(results):
    """
    Get a list of values from a single-column ResultProxy.
    """
    return [x for x, in results]


_PG_SERIALIZATION_FAILURE = '40001'


def serializable_retry(action, limit=16):
    """
    Runs an action accepting a `Connection` parameter in a serializable
    transaction, retrying it up to `limit` times.
    """
    with engine.connect() as db:
        db = db.execution_options(isolation_level='SERIALIZABLE')

        for i in itertools.count(1):
            try:
                with db.begin():
                    return action(db)
            except OperationalError as e:
                if i == limit or e.orig.pgcode != _PG_SERIALIZATION_FAILURE:
                    raise


with open(os.path.join(macro.MACRO_APP_ROOT, "version.txt")) as f:
    CURRENT_SHA = f.read().strip()


# Caching all templates. Parsing templates is slow; we don't need to do it all
# the time and there's plenty of memory for storing the compiled templates.
_template_cache = {}


def _compile(template_name):
    """
    Compiles a template file and returns the result.
    """
    template = _template_cache.get(template_name)

    if template is None or reload_templates:
        _template_cache[template_name] = template = Template(
            pkgutil.get_data(__name__, 'templates/' + template_name).decode('utf-8'),
            filename=template_name,
            globals={
                "STR": str,
                "LOGIN": get_sysname,
                "USER_TYPE": user_type,
                "ARROW": get_arrow,
                "LOCAL_TIME": _get_local_time_html,
                "ISO8601_DATE": iso8601_date,
                "PRICE": text_price_amount,
                "SYMBOL": text_price_symbol,
                "TITLE": titlebar,
                "RENDER": render,
                "COMPILE": _compile,
                "MARKDOWN": text.markdown,
                "MARKDOWN_EXCERPT": text.markdown_excerpt,
                "SUMMARIZE": summarize,
                "SHA": CURRENT_SHA,
                "NOW": get_time,
                "THUMB": thumb_for_sub,
                "WEBP_THUMB": webp_thumb_for_sub,
                "M": macro,
                "R": ratings,
                "SLUG": text.slug_for,
                "QUERY_STRING": query_string,
                "INLINE_JSON": html.inline_json,
                "PATH": _get_path,
                "arrow": arrow,
                "constants": libweasyl.constants,
                "format": format,
                "getattr": getattr,
                "json": json,
                "sorted": sorted,
                "staff": staff,
                "resource_path": get_resource_path,
            })

    return template


def render(template_name, argv=()):
    """
    Renders a template and returns the resulting HTML.
    """
    template = _compile(template_name)
    return str(template(*argv))


def titlebar(title, backtext=None, backlink=None):
    return render("common/stage_title.html", [title, backtext, backlink])


def errorpage_html(userid, message_html, links=None, request_id=None, **extras):
    return webpage(userid, "error/error.html", [message_html, links, request_id], **extras)


def errorpage(userid, code=None, links=None, request_id=None, **extras):
    if code is None:
        code = errorcode.unexpected

    return errorpage_html(userid, text.markdown(code), links, request_id, **extras)


def webpage(userid, template, argv=(), options=(), **extras):
    page = common_page_start(userid, options=options, **extras)
    page.append(render(template, argv))

    return common_page_end(userid, page, options=options)


def get_userid():
    """
    Returns the userid corresponding to the current request, if any.
    """
    return get_current_request().userid


_ORIGIN = config_obj.get('general', 'origin')


def is_csrf_valid(request):
    return request.headers.get('origin') == _ORIGIN


@region.cache_on_arguments(namespace='v3')
def _get_all_config(userid):
    """
    Queries for, and returns, common user configuration settings.

    :param userid: The userid to query.
    :return: A dict(), containing the following keys/values:
      is_banned: Boolean. Is the user currently banned?
      is_suspended: Boolean. Is the user currently suspended?
      is_vouched_for: Boolean. Is the user vouched for?
      profile_configuration: CharSettings/string. Configuration options in the profile.
      jsonb_settings: JSON/dict. Profile settings set via jsonb_settings.
    """
    row = engine.execute("""
        SELECT EXISTS (SELECT FROM permaban WHERE permaban.userid = %(userid)s) AS is_banned,
               EXISTS (SELECT FROM suspension WHERE suspension.userid = %(userid)s) AS is_suspended,
               lo.voucher IS NOT NULL AS is_vouched_for,
               pr.config AS profile_configuration,
               pr.jsonb_settings
        FROM login lo INNER JOIN profile pr USING (userid)
        WHERE userid = %(userid)s
    """, userid=userid).first()

    return dict(row)


def get_config(userid):
    """ Gets user configuration from the profile table (profile.config)"""
    if not userid:
        return ""
    return _get_all_config(userid)['profile_configuration']


def get_login_settings(userid):
    """ Returns a Boolean pair in the form of (is_banned, is_suspended)"""
    r = _get_all_config(userid)
    return r['is_banned'], r['is_suspended']


def is_vouched_for(userid):
    return _get_all_config(userid)['is_vouched_for']


def get_profile_settings(userid):
    from weasyl.profile import ProfileSettings

    if not userid:
        jsonb = {}
    else:
        jsonb = _get_all_config(userid)['jsonb_settings']

        if jsonb is None:
            jsonb = {}

    return ProfileSettings(jsonb)


def get_config_rating(userid):
    config = get_config(userid)
    if 'p' in config:
        return ratings.EXPLICIT.code
    elif 'a' in config:
        return ratings.MATURE.code
    else:
        return ratings.GENERAL.code


def get_rating(userid):
    if not userid:
        return ratings.GENERAL.code

    if is_sfw_mode():
        return ratings.GENERAL.code

    return get_config_rating(userid)


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
    if target is None:
        return 0

    if isinstance(target, numbers.Number):
        return int(target)

    try:
        return int("".join(i for i in target if i.isdigit()))
    except ValueError:
        return 0


def get_targetid(*argv):
    for i in argv:
        if i:
            return i


def get_search_tag(target):
    target = "".join(i for i in target if ord(i) < 128)
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
    id_hash = hashlib.sha1(b"%i" % (charid,)).hexdigest()
    return "/".join([id_hash[i:i + 2] for i in range(0, 11, 2)]) + "/"


def get_character_directory(charid):
    return macro.MACRO_SYS_CHAR_PATH + _get_hash_path(charid)


@region.cache_multi_on_arguments(should_cache_fn=bool)
def _get_userids(*sysnames):
    result = engine.execute(
        "SELECT login_name, userid FROM login WHERE login_name = ANY (%(names)s)"
        " UNION ALL SELECT alias_name, userid FROM useralias WHERE alias_name = ANY (%(names)s)"
        " UNION ALL SELECT login_name, userid FROM username_history WHERE active AND login_name = ANY (%(names)s)",
        names=list(sysnames),
    )

    sysname_userid = dict(result.fetchall())

    return [sysname_userid.get(sysname, 0) for sysname in sysnames]


def get_userids(usernames):
    ret = {}
    lookup_usernames = []
    sysnames = []

    for username in usernames:
        sysname = get_sysname(username)

        if sysname:
            lookup_usernames.append(username)
            sysnames.append(sysname)
        else:
            ret[username] = 0

    ret.update(zip(lookup_usernames, _get_userids(*sysnames)))

    return ret


def get_userid_list(target):
    usernames = target.split(";")
    return [userid for userid in get_userids(usernames).values() if userid != 0]


def get_ownerid(submitid=None, charid=None, journalid=None):
    if submitid:
        return engine.scalar("SELECT userid FROM submission WHERE submitid = %(id)s", id=submitid)
    if charid:
        return engine.scalar("SELECT userid FROM character WHERE charid = %(id)s", id=charid)
    if journalid:
        return engine.scalar("SELECT userid FROM journal WHERE journalid = %(id)s", id=journalid)


def get_address():
    request = get_current_request()
    return request.client_addr


def _get_path():
    return get_current_request().path_qs


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


def get_arrow(unixtime):
    """
    Get an `Arrow` from a Weasyl timestamp, time-zone-aware `datetime`, or `Arrow`.
    """
    if isinstance(unixtime, (int, float)):
        unixtime -= _UNIXTIME_OFFSET
    elif not isinstance(unixtime, (arrow.Arrow, datetime.datetime)) or unixtime.tzinfo is None:
        raise ValueError("unixtime must be supported numeric or datetime")  # pragma: no cover

    return arrow.get(unixtime)


def _get_local_time_html(target, template):
    target = get_arrow(target)
    date_text = target.format("MMMM D, YYYY")
    time_text = target.format("HH:mm:ss ZZZ")
    content = template.format(
        date=f'<span class="local-time-date">{date_text}</span>',
        time=f'<span class="local-time-time">{time_text}</span>',
        date_text=date_text,
    )
    return f'<time datetime="{iso8601(target)}"><local-time data-timestamp="{target.int_timestamp}">{content}</local-time></time>'


def iso8601_date(target):
    """
    Converts a Weasyl timestamp to an ISO 8601 date (yyyy-mm-dd).

    NB: Target is offset by _UNIXTIME_OFFSET

    :param target: The target Weasyl timestamp to convert.
    :return: An ISO 8601 string representing the date of `target`.
    """
    return arrow.get(target - _UNIXTIME_OFFSET).format("YYYY-MM-DD")


def convert_unixdate(day, month, year):
    """
    Returns the unixtime corresponding to the beginning of the specified date; if
    the date is not valid, None is returned.
    """
    day, month, year = (get_int(i) for i in [day, month, year])

    try:
        ret = int(time.mktime(datetime.date(year, month, day).timetuple()))
    except ValueError:
        return None
    # range of a postgres integer
    if ret > 2147483647 or ret < -2147483648:
        return None
    return ret


def convert_age(target):
    return (get_time() - target) // 31556926


def age_in_years(birthdate):
    """
    Determines an age in years based off of the given arrow.Arrow birthdate
    and the current date.
    """
    now = arrow.utcnow()
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


def _posts_count_query_basic(table):
    return (
        f"SELECT '{table}' AS post_type, rating, friends_only, count(*) FROM {table}"
        " WHERE userid = %(userid)s"
        " AND NOT hidden"
        " GROUP BY rating, friends_only"
    )


_POSTS_COUNT_QUERY = " UNION ALL ".join((
    _posts_count_query_basic("submission"),
    _posts_count_query_basic("journal"),
    _posts_count_query_basic("character"),
    (
        "SELECT 'collection' AS post_type, rating, friends_only, count(*)"
        " FROM collection INNER JOIN submission USING (submitid)"
        " WHERE collection.userid = %(userid)s"
        " AND NOT hidden"
        " AND collection.settings !~ '[pr]'"
        " GROUP BY rating, friends_only"
    ),
))


@dataclass(frozen=True, slots=True)
class PostsCountKey:
    post_type: Literal["submission", "journal", "character", "collection"]
    rating: Literal[10, 30, 40]


@region.cache_on_arguments()
def cached_posts_count(userid):
    return [*map(dict, engine.execute(_POSTS_COUNT_QUERY, userid=userid))]


def cached_posts_count_invalidate_multi(userids):
    namespace = None
    cache_keys = [*map(region.function_key_generator(namespace, cached_posts_count), userids)]
    region.delete_multi(cache_keys)


def posts_count(userid, *, friends: bool):
    result = defaultdict(int)

    for row in cached_posts_count(userid):
        if friends or not row["friends_only"]:
            key = PostsCountKey(
                post_type=row["post_type"],
                rating=row["rating"],
            )
            result[key] += row["count"]

    return result


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


def get_max_post_rating(userid):
    return max((key.rating for key, count in posts_count(userid, friends=True).items() if count), default=ratings.GENERAL.code)


def _is_sfw_locked(userid):
    """
    Determine whether SFW mode has no effect for the specified user.

    If the standard rating preference is General and the user has no posts above that rating, SFW mode has no effect.
    """
    config_rating = get_config_rating(userid)

    if config_rating > ratings.GENERAL.code:
        return False

    max_post_rating = get_max_post_rating(userid)
    return max_post_rating is not None and max_post_rating <= config_rating


def page_header_info(userid):
    from weasyl import media
    sfw = get_current_request().cookies.get('sfwmode', 'nsfw') == 'sfw'
    return {
        "welcome": _page_header_info(userid),
        "userid": userid,
        "username": get_display_name(userid),
        "user_media": media.get_user_media(userid),
        "sfw": sfw,
        "sfw_locked": _is_sfw_locked(userid),
    }


def common_page_start(userid, options=(), **extended_options):
    userdata = None
    if userid:
        userdata = page_header_info(userid)

    data = render(
        "common/page_start.html", [userdata, options, extended_options])

    return [data]


def common_page_end(userid, page, options=()):
    data = render("common/page_end.html", (options,))
    page.append(data)
    return "".join(page)


def common_status_check(userid):
    """
    Returns the name of the script to which the user should be redirected
    if required.
    """
    if not userid:
        return None

    is_banned, is_suspended = get_login_settings(userid)

    if is_banned:
        return "banned"
    if is_suspended:
        return "suspended"

    return None


def common_status_page(userid, status):
    """
    Raise the redirect to the script returned by common_status_check() or render
    the appropriate site status error page.
    """
    assert status in ('banned', 'suspended')

    from weasyl import moderation, login

    if status == 'banned':
        message = moderation.get_ban_message(userid)
    elif status == 'suspended':
        message = moderation.get_suspension_message(userid)

    login.signout(get_current_request())

    response = Response(errorpage(userid, message))
    response.delete_cookie('WZL')
    response.delete_cookie('sfwmode')
    return response


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

    engine.execute("DELETE FROM views WHERE viewed_at < now() - INTERVAL '15 minutes'")

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
            return None if root else get_resource_path("img/default-visual.png")
    # Character thumbnail selection
    elif feature == "char/.thumb":
        result.append("%i.new.thumb" % (targetid,))

    return "".join(result)


def cdnify_url(url):
    cdn_root = config_read_setting("cdn_root")
    if not cdn_root:
        return url

    return urljoin(cdn_root, url)


def get_resource_path(resource):
    if reload_assets:
        _load_resources()

    return '/' + resource_paths[resource]


def get_resource_url(resource):
    """
    Get a full URL for a resource.

    Useful for <meta name="og:image">, for example.
    """
    return 'https://www.weasyl.com' + get_resource_path(resource)


DEFAULT_SUBMISSION_THUMBNAIL = [
    dict.fromkeys(
        ['display_url', 'file_url'],
        get_resource_path('img/default-visual.png'),
    ),
]

DEFAULT_AVATAR = [
    dict.fromkeys(
        ['display_url', 'file_url'],
        get_resource_path('img/default-avatar.jpg'),
    ),
]


def absolutify_url(url):
    cdn_root = config_read_setting("cdn_root")
    if cdn_root and url.startswith(cdn_root):
        return url

    return urljoin(get_current_request().application_url, url)


def summarize(s, max_length=200):
    if len(s) > max_length:
        return s[:max_length - 1].rstrip() + '\N{HORIZONTAL ELLIPSIS}'
    return s


def clamp(val, lower_bound, upper_bound):
    return min(max(val, lower_bound), upper_bound)


def query_string(query):
    pairs = []

    for key, value in query.items():
        if isinstance(value, (tuple, list, set)):
            for subvalue in value:
                pairs.append((key, subvalue))
        elif value:
            pairs.append((key, value))

    return urlencode(pairs)


def _requests_wrapper(func_name):
    func = getattr(requests, func_name)

    def wrapper(*a, **kw):
        try:
            return func(*a, **kw)
        except Exception as e:
            w = WeasylError('httpError', level='info')
            w.error_suffix = 'The original error was: %s' % (e,)
            raise w from e

    return wrapper


http_get = _requests_wrapper('get')
http_post = _requests_wrapper('post')


def metric(*a, **kw):
    pass


def iso8601(unixtime):
    return (
        get_arrow(unixtime)
        .isoformat(timespec='seconds')
        .replace('+00:00', 'Z')
    )


def parse_iso8601(s):
    return arrow.Arrow.strptime(s, '%Y-%m-%dT%H:%M:%SZ').int_timestamp + _UNIXTIME_OFFSET


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


def webp_thumb_for_sub(submission):
    """
    Given a submission dict containing sub_media, sub_type and userid,
    returns the appropriate WebP media item to use as a thumbnail.

    Params:
        submission: The submission.

    Returns:
        The sub media to use as a thumb, or None.
    """
    user_id = get_userid()
    profile_settings = get_profile_settings(user_id)
    disable_custom_thumb = (
        profile_settings.disable_custom_thumbs and
        submission.get('subtype', 9999) < 2000 and
        submission['userid'] != user_id
    )

    if not disable_custom_thumb and 'thumbnail-custom' in submission['sub_media']:
        return None

    thumbnail_generated_webp = submission['sub_media'].get('thumbnail-generated-webp')
    return thumbnail_generated_webp and thumbnail_generated_webp[0]

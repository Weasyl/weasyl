from __future__ import annotations

import functools
import os
import time
import hashlib
import itertools
import json
import numbers
import datetime
import pkgutil
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from typing import NewType
from typing import overload
from urllib.parse import urlencode, urljoin

import arrow
from pyramid.threadlocal import get_current_request
import requests
import sqlalchemy as sa
import sqlalchemy.orm
from ada_url import URL
from prometheus_client import Histogram
from psycopg2.errorcodes import SERIALIZATION_FAILURE
from pyramid.response import Response
from sqlalchemy.exc import OperationalError
from web.template import Template

import libweasyl.constants
from libweasyl.cache import region
from libweasyl.legacy import UNIXTIME_OFFSET as _UNIXTIME_OFFSET
from libweasyl.models.tables import metadata as meta
from libweasyl.text import slug_for
from libweasyl.text import summarize
from libweasyl import html, text, ratings, staff

from weasyl import cards
from weasyl import config
from weasyl import errorcode
from weasyl import macro
from weasyl import metrics
from weasyl import turnstile
from weasyl.config import config_obj, config_read_setting
from weasyl.error import WeasylError
from weasyl.forms import parse_sysname
from weasyl.forms import parse_sysname_list
from weasyl.users import Username


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
                if i == limit or e.orig.pgcode != SERIALIZATION_FAILURE:
                    raise


def _sysname_for_stored_username(s: str) -> str:
    return Username.from_stored(s).sysname


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
                "LOGIN": _sysname_for_stored_username,
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

                "CARD_WIDTHS": cards.get_widths,
                "get_card_viewer": get_card_viewer,

                "M": macro,
                "R": ratings,
                "SLUG": slug_for,
                "QUERY_STRING": query_string,
                "INLINE_JSON": html.inline_json,
                "ORIGIN": ORIGIN,
                "PATH": _get_path,
                "arrow": arrow,
                "constants": libweasyl.constants,
                "format": format,
                "getattr": getattr,
                "json": json,
                "map": map,
                "sorted": sorted,
                "staff": staff,
                "turnstile": turnstile,
                "resource_path": get_resource_path,
                "zip": zip,

                "DEFAULT_LOGIN_FORM": DEFAULT_LOGIN_FORM,
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


ORIGIN = config_obj.get('general', 'origin')


def is_csrf_valid(request):
    return request.headers.get('origin') == ORIGIN


def path_redirect(path_qs: str) -> str:
    """
    Return an absolute URL for an internal redirect within the application’s origin.
    """
    return ORIGIN + path_qs


@region.cache_on_arguments(namespace='v4')
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
      premium: Boolean. Is the user a premium user?
    """
    row = engine.execute("""
        SELECT EXISTS (SELECT FROM permaban WHERE permaban.userid = %(userid)s) AS is_banned,
               EXISTS (SELECT FROM suspension WHERE suspension.userid = %(userid)s) AS is_suspended,
               lo.voucher IS NOT NULL AS is_vouched_for,
               pr.config AS profile_configuration,
               pr.jsonb_settings,
               pr.premium
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


def get_config_rating(userid: int) -> ratings.Rating:
    config = get_config(userid)
    if 'p' in config:
        return ratings.EXPLICIT
    elif 'a' in config:
        return ratings.MATURE
    else:
        return ratings.GENERAL


def get_rating_obj(userid: int) -> ratings.Rating:
    if not userid:
        return ratings.GENERAL

    if is_sfw_mode():
        return ratings.GENERAL

    return get_config_rating(userid)


def get_rating(userid: int) -> int:
    return get_rating_obj(userid).code


def is_sfw_mode():
    """
    determine whether the current session is in SFW mode
    :return: TRUE if sfw or FALSE if nsfw
    """
    return get_current_request().cookies.get('sfwmode', "nsfw") == "sfw"


def get_premium(userid: int) -> bool:
    if not userid:
        return False

    return _get_all_config(userid)["premium"]


@region.cache_on_arguments(should_cache_fn=bool)
@record_timing
def _get_display_name(userid: int) -> str | None:
    """
    Return the display name assiciated with `userid`; if no such user exists,
    return None.
    """
    return engine.scalar("SELECT username FROM profile WHERE userid = %(user)s", user=userid)


def get_display_name(userid: int) -> str:
    username = _get_display_name(userid)

    if username is None:
        raise WeasylError("Unexpected")

    return username


def try_get_username(userid: int) -> Username | None:
    username = _get_display_name(userid)
    return Username.from_stored(username) if username is not None else None


def get_username(userid: int) -> Username:
    return Username.from_stored(get_display_name(userid))


username_invalidate = _get_display_name.invalidate
"""
Invalidate the cached username for a user.
"""


def get_int(target) -> int:
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


def get_userids(usernames: Iterable[str]) -> Mapping[str, int]:
    ret: dict[str, int] = {}
    lookup_usernames: list[str] = []
    sysnames: list[str] = []

    for username in usernames:
        sysname = parse_sysname(username)

        if sysname is not None:
            lookup_usernames.append(username)
            sysnames.append(sysname)
        else:
            ret[username] = 0

    ret.update(zip(lookup_usernames, _get_userids(*sysnames)))

    return ret


def get_userid_list(target: str) -> list[int]:
    return [userid for userid in get_userids(parse_sysname_list(target)).values() if userid != 0]


@overload
def get_ownerid(*, submitid: int) -> int | None:
    ...


@overload
def get_ownerid(*, charid: int) -> int | None:
    ...


@overload
def get_ownerid(*, journalid: int) -> int | None:
    ...


def get_ownerid(*, submitid=None, charid=None, journalid=None):
    if submitid:
        return engine.scalar("SELECT userid FROM submission WHERE submitid = %(id)s", id=submitid)
    if charid:
        return engine.scalar("SELECT userid FROM character WHERE charid = %(id)s", id=charid)
    if journalid:
        return engine.scalar("SELECT userid FROM journal WHERE journalid = %(id)s", id=journalid)

    return None


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


HttpUrl = NewType("HttpUrl", URL)


def text_fix_url(s: str) -> HttpUrl | None:
    """
    Normalize a user-provided external web link to a URL that always uses `http:` or `https:` (`https:` is assumed when no explicit protocol is provided). The result is safe to use as the `href` attribute of a link in the same sense as `libweasyl.defang`. This also normalizes the domain name to lowercase and Punycode.

    Disallows some weird enough URLs that probably don’t have legitimate uses, indicating a misinterpretation compared to user intent:
    - URLs containing credentials (`https://username:password@…/`)
    - URLs with fully-qualified domain names (`https://example.com./`)
    - URLs with single-component domain names (`https://example/`)
    """
    s = s.strip()

    try:
        url = URL(s)
    except ValueError:
        try:
            url = URL("https://" + s)
        except ValueError:
            return None

    if (
        url.protocol in ["http:", "https:"]
        and not url.username
        and not url.password
        and "." in url.hostname
        and not url.hostname.endswith(".")
    ):
        return HttpUrl(url)

    return None


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


def private_messages_unread_count(userid: int) -> int:
    return engine.scalar(
        "SELECT COUNT(*) FROM message WHERE otherid = %(user)s AND settings ~ 'u'", user=userid)


@region.cache_on_arguments()
def get_last_read_updateid(userid: int) -> int | None:
    return engine.scalar("""
        SELECT last_read_updateid
        FROM login
        WHERE userid = %(user)s
    """, user=userid)


@region.cache_on_arguments()
def get_updateids() -> list[int]:
    results = engine.execute("""
        SELECT updateid
        FROM siteupdate
        ORDER BY updateid DESC
    """).fetchall()

    return [result.updateid for result in results]


def site_update_unread_count(userid: int) -> int:
    return [*get_updateids(), None].index(get_last_read_updateid(userid))


notification_count_time = metrics.CachedMetric(Histogram("weasyl_notification_count_fetch_seconds", "notification counts fetch time", ["cached"]))


@metrics.separate_timing
@notification_count_time.cached
@region.cache_on_arguments(expiration_time=180)
@notification_count_time.uncached
def _page_header_info(userid):
    messages = private_messages_unread_count(userid)
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


def page_header_info_invalidate_multi(userids):
    namespace = None
    cache_keys = [*map(region.function_key_generator(namespace, _page_header_info), userids)]
    region.delete_multi(cache_keys)


def _get_max_post_rating(userid: int) -> int:
    return max((key.rating for key, count in posts_count(userid, friends=True).items() if count), default=ratings.GENERAL.code)


def _is_sfw_locked(userid: int) -> bool:
    """
    Determine whether SFW mode has no effect for the specified user.

    If the standard rating preference is General and the user has no posts above that rating, SFW mode has no effect.
    """
    config_rating = get_config_rating(userid)

    if config_rating > ratings.GENERAL:
        return False

    max_post_rating = _get_max_post_rating(userid)
    return max_post_rating is not None and max_post_rating <= config_rating.code


def page_header_info(userid):
    from weasyl import media
    sfw = get_current_request().cookies.get('sfwmode', 'nsfw') == 'sfw'
    notification_counts = _page_header_info(userid)
    unread_updates = site_update_unread_count(userid)
    return {
        "welcome": notification_counts,
        "unread_updates": unread_updates,
        "updateids": get_updateids(),
        "userid": userid,
        "username": get_username(userid),
        "user_media": media.get_user_media(userid),
        "sfw": sfw,
        "sfw_locked": _is_sfw_locked(userid),
    }


@dataclass(frozen=True, slots=True)
class LoginForm:
    username: str
    sfw: bool


DEFAULT_LOGIN_FORM = LoginForm(username="", sfw=False)


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


def shows_statistics(*, viewer: int, target: int) -> bool:
    return "i" not in get_config(target) or viewer in staff.MODS


Viewable = Literal["submissions", "characters", "journals", "users"]

_content_types: Mapping[Viewable, tuple[int, str, str]] = {
    'submissions': (110, 'submission', 'submitid'),
    'characters': (120, 'character', 'charid'),
    'journals': (130, 'journal', 'journalid'),
    'users': (210, 'profile', 'userid'),
}


def common_view_content(
    userid: int,
    targetid: int,
    feature: Viewable,
) -> int | None:
    """
    Records a page view, returning the updated view count, or `None` if it didn’t change.
    """
    typeid, table, pk = _content_types[feature]

    if feature == "users":
        if targetid == userid:
            return None
    elif userid and get_ownerid(**{pk: targetid}) == userid:
        return None

    if userid:
        viewer = 'user:%d' % (userid,)
    else:
        viewer = get_address()

    engine.execute("DELETE FROM views WHERE viewed_at < now() - INTERVAL '15 minutes'")

    result = engine.execute(
        'INSERT INTO views (viewer, targetid, type) VALUES (%(viewer)s, %(targetid)s, %(type)s) ON CONFLICT DO NOTHING',
        viewer=viewer, targetid=targetid, type=typeid)

    if result.rowcount == 0:
        return None

    return engine.scalar(
        f"UPDATE {table}"
        " SET page_views = page_views + 1"
        f" WHERE {pk} = %(id)s"
        " RETURNING page_views",
        id=targetid,
    )


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


def _requests_wrapper(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        try:
            return func(*a, **kw)
        except Exception as e:
            raise WeasylError('httpError', level='info') from e

    return wrapper


http_get = _requests_wrapper(requests.get)


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


_default_thumbs = cards.get_default_thumbnails(get_resource_path)


def get_card_viewer() -> cards.Viewer:
    """
    Gets the card-viewing experience (thumbnail preferences, essentially) for the current user.
    """
    userid = get_userid()
    profile_settings = get_profile_settings(userid)
    return cards.Viewer(
        userid=userid,
        disable_custom_thumbs=profile_settings.disable_custom_thumbs,
        default_thumbs=_default_thumbs,
    )

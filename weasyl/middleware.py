import html
import itertools
import re
import secrets
import time
import traceback
from datetime import datetime, timedelta, timezone

import multipart
from prometheus_client import Histogram
from pyramid.decorator import reify
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPServiceUnavailable,
    HTTPUnauthorized,
)
from pyramid.request import Request as Request_
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from sqlalchemy import event
from sqlalchemy.engine import Engine
from web.utils import storify
from webob.multidict import MultiDict, NoVars

from libweasyl import staff
from libweasyl.cache import ThreadCacheProxy
from weasyl import define as d
from weasyl import errorcode
from weasyl import orm
from weasyl.error import WeasylError


# should match Nginx configuration
_CLIENT_MAX_BODY_SIZE = 55 * 1024 * 1024


class FieldStorage:
    """
    Wraps a `multipart.MultipartPart` to look like a `cgi.FieldStorage`, which it almost does already.
    """

    def __init__(self, multipart_part, /):
        self._wrapped = multipart_part

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

    @property
    def value(self):
        return self._wrapped.raw


class Request(Request_):

    @property
    def request_body_tempfile_limit(self):
        raise NotImplementedError

    def decode(self):
        raise NotImplementedError

    @property
    def body_file(self):
        return self.body_file_raw

    @property
    def body_file_seekable(self):
        raise NotImplementedError

    @property
    def body(self):
        r = self.body_file_raw.read()
        self.body_file_raw = None
        return r

    @reify
    def POST(self):
        # derived from WebOb code
        # https://github.com/Pylons/webob/blob/259230aa2b8b9cf675c996e157c5cf021c256059/src/webob/request.py#L773
        # licenses/webob.txt
        """
        Return a MultiDict containing all the variables from a form request.
        """
        if self.method not in ("POST", "PUT"):
            return NoVars("not POST or PUT request")

        environ = self.environ

        if not environ.get("wsgi.input_terminated", False):
            raise Exception("need wsgi.input_terminated to use multipart")

        # Let MultiDict throw if content with no Content-Type.
        # An empty request with no Content-Type is produced by WebTest, at least.
        if not environ.get("CONTENT_TYPE") and environ.get("CONTENT_LENGTH") == "0":
            return NoVars("empty request body")

        # XXX: multipart.parse_form_data moves fields to files when they’re too large.
        # this could cause the values of a field to spontaneously reorder.
        # luckily, they also change type when that happens, which should cause an error.
        forms, files = multipart.parse_form_data(
            environ,
            strict=True,
            # never buffer to disk. for malicious requests, 55 MiB * 12 concurrent requests = 660 MiB.
            # for legitimate requests, we’re loading the entire image into memory anyway.
            mem_limit=_CLIENT_MAX_BODY_SIZE,
            memfile_limit=_CLIENT_MAX_BODY_SIZE,  # ≥ mem_limit in order to never create a temporary file
        )
        return MultiDict(
            itertools.chain(
                forms.iterallitems(),
                ((k, FieldStorage(v)) for k, v in files.iterallitems()),
            )
        )

    def copy(self):
        raise NotImplementedError

    @property
    def is_body_seekable(self):
        return False

    def make_body_seekable(self):
        raise NotImplementedError

    def copy_body(self):
        raise NotImplementedError

    def make_tempfile(self):
        raise NotImplementedError


def utf8_path_tween_factory(handler, registry):
    """
    A tween to reject requests with invalid UTF-8 in the path early.
    """
    def utf8_path_tween(request):
        try:
            request.path_info
        except UnicodeDecodeError:
            return HTTPBadRequest()

        return handler(request)

    return utf8_path_tween


def cache_clear_tween_factory(handler, registry):
    """
    A tween to clear the thread local cache.
    """
    def cache_clear_tween(request):
        try:
            return handler(request)
        finally:
            ThreadCacheProxy.zap_cache()
    return cache_clear_tween


request_duration = Histogram(
    "weasyl_request_duration_seconds",
    "total request time",
    ["route"],
    # `Histogram.DEFAULT_BUCKETS`, extended up to the Gunicorn worker timeout
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, float("inf")),
)


def db_timer_tween_factory(handler, registry):
    """
    A tween that records timing information in the headers of a response.
    """
    # register all labels for the `weasyl_request_duration_seconds` metric in advance
    for route in registry.introspector.get_category("routes"):
        request_duration.labels(route=route["introspectable"].discriminator)

    def db_timer_tween(request):
        started_at = time.perf_counter()
        request.excluded_time = 0.0
        request.sql_times = []
        request.memcached_times = []
        resp = handler(request)
        time_total = time.perf_counter() - started_at - request.excluded_time
        request_duration.labels(route=request.matched_route.name if request.matched_route is not None else "none").observe(time_total, exemplar={
            "sql_queries": "%d" % (len(request.sql_times),),
            "sql_seconds": "%.3f" % (sum(request.sql_times),),
            "memcached_queries": "%d" % (len(request.memcached_times),),
            "memcached_seconds": "%.3f" % (sum(request.memcached_times),),
        })
        return resp
    return db_timer_tween


def session_tween_factory(handler, registry):
    """
    A tween that sets a weasyl_session on a request.
    """
    def remove_session_cookie_callback(request, response):
        if request.weasyl_session is None:
            response.delete_cookie('WZL')

    _SESSION_LAST_ACTIVE_UPDATE_THRESHOLD = timedelta(minutes=10)

    # TODO(hyena): Investigate a pyramid session_factory implementation instead.
    def session_tween(request):
        sess_obj = None

        if cookie := request.cookies.get('WZL'):
            sess_obj = request.pg_connection.query(orm.Session).get(cookie)

            if sess_obj is None:
                # remove the invalid cookie as part of the response, if the request didn’t result in a new session being created
                request.add_response_callback(remove_session_cookie_callback)
            else:
                request.pg_connection.expunge(sess_obj)

                if sess_obj.last_active is None or datetime.now(timezone.utc) - sess_obj.last_active > _SESSION_LAST_ACTIVE_UPDATE_THRESHOLD:
                    d.engine.execute(
                        "UPDATE sessions SET last_active = now() WHERE sessionid = %(sessionid)s",
                        {"sessionid": sess_obj.sessionid},
                    )

        request.weasyl_session = sess_obj

        return handler(request)

    return session_tween


def query_debug_tween_factory(handler, registry):
    """
    A tween that allows developers to view timing per query.
    """
    def callback(request, response):
        if not hasattr(request, 'weasyl_session') or request.userid not in staff.DEVELOPERS:
            return

        class ParameterCounter:
            def __init__(self):
                self.next = 1
                self.ids = {}

            def __getitem__(self, name):
                id = self.ids.get(name)

                if id is None:
                    id = self.ids[name] = self.next
                    self.next += 1

                return '$%i' % (id,)

        debug_rows = []

        for statement, t in request.query_debug:
            statement = ' '.join(statement.split()).replace('( ', '(').replace(' )', ')') % ParameterCounter()
            debug_rows.append('<tr><td>%.1f ms</td><td><code>%s</code></td></tr>' % (t * 1000, html.escape(statement)))

        response.text += ''.join(
            ['<table style="background: white; border-collapse: separate; border-spacing: 1em; table-layout: auto; margin: 1em; font-family: sans-serif">']
            + debug_rows
            + ['</table>']
        )

    def query_debug_tween(request):
        if 'query_debug' in request.GET:
            request.query_debug = []
            request.add_response_callback(callback)

        return handler(request)

    return query_debug_tween


def status_check_tween_factory(handler, registry):
    """
    A tween that checks if the weasyl user is banned, suspended, etc. and redirects appropriately.

    Rather than performing these checks on every view.
    """
    def status_check_tween(request):
        status = d.common_status_check(request.userid)
        if status:
            return d.common_status_page(request.userid, status)
        return handler(request)
    return status_check_tween


def database_session_cleanup_tween_factory(handler, registry):
    """
    A tween that cleans up the thread-local database session after every request.
    """
    def database_session_cleanup_tween(request):
        def cleanup(request):
            d.sessionmaker.remove()

        request.add_finished_callback(cleanup)
        return handler(request)

    return database_session_cleanup_tween


# The value of the `Link` header that will be set in the `preload_tween_factory` function below.
# Only constructed once on application load; not affected by `WEASYL_RELOAD_ASSETS`.
_WEBPAGE_PRELOADS_LINK = ", ".join([
    # CSS
    *(
        f"<{d.get_resource_path(item)}>;rel=preload;as=style" for item in [
            "css/site.css",
        ]
    ),

    # JS
    *(
        f"<{d.get_resource_path(item)}>;rel=preload;as=script" for item in [
            "js/main.js",
        ]
    ),
])


def preload_tween_factory(handler, registry):
    """
    Add the `Link` header to outgoing responses to preload resources needed on every webpage, which is served ahead of time by Cloudflare as an HTTP 103 Early Hints message.
    """
    def preload_tween(request):
        resp = handler(request)

        content_type = resp.headers.get('Content-Type')

        if content_type is not None and content_type.startswith("text/html"):
            resp.headers['Link'] = _WEBPAGE_PRELOADS_LINK

        return resp
    return preload_tween


# Properties and methods to enhance the pyramid `request`.
def pg_connection_request_property(request):
    """
    Used for the reified pg_connection property on weasyl requests.
    """
    return d.sessionmaker()


def userid_request_property(request):
    """
    Used for the userid property on weasyl requests.
    """
    api_token = request.headers.get('X_WEASYL_API_KEY')
    authorization = request.headers.get('AUTHORIZATION')
    if api_token is not None:
        # TODO: If reification of userid becomes an issue (e.g. because of userid changing after sign-in) revisit this.
        # It's possible that we don't need to reify the entire property, but just cache the result of this query in a
        # cache on arguments inner function.
        userid = d.engine.scalar("SELECT userid FROM api_tokens WHERE token = %(token)s", token=api_token)
        if not userid:
            raise HTTPUnauthorized(www_authenticate=('Weasyl-API-Key', 'realm="Weasyl"'))
        return userid

    elif authorization:
        raise HTTPServiceUnavailable()

    else:
        sess = request.weasyl_session
        # session is None for a guest
        userid = sess and sess.userid
        # session’s userid is None for 2FA in progress
        return userid or 0


def web_input_request_method(request, *required, **kwargs):
    """
    Callable that processes the pyramid request.params multidict into a web.py storage object
    in the style of web.input().
    TODO: Replace usages of this method with accessing request directly.

    @param request: The pyramid request object.
    @param kwargs: Default values. If a default value is a list, it indicates that multiple
        values of that key should be collapsed into a list.
    @return: A dictionary-like object in the fashion of web.py's web.input()
    """
    return storify(request.params.mixed(), *required, **kwargs)


def _redact_match(match):
    prefix, secret = match.groups()
    return "%s[%d redacted]" % (prefix, len(secret))


def _log_request(request, *, request_id=None):
    env = {}

    if request_id is not None:
        env["request_id"] = request_id

    env["user_id"] = request.userid

    env.update(request.environ)

    # remove redundant data
    env.pop("webob._parsed_cookies", None)
    env.pop("webob._parsed_query_vars", None)

    # don't log session cookies
    if "HTTP_COOKIE" in env:
        env["HTTP_COOKIE"] = re.sub(
            r'(WZL="?)([\w\-]+)',
            _redact_match,
            env["HTTP_COOKIE"],
            re.ASCII,
        )

    # don't log API keys or OAuth tokens
    if "HTTP_X_WEASYL_API_KEY" in env:
        env["HTTP_X_WEASYL_API_KEY"] = "[%d redacted]" % (len(env["HTTP_X_WEASYL_API_KEY"]),)

    if "HTTP_AUTHORIZATION" in env:
        env["HTTP_AUTHORIZATION"] = re.sub(
            r'((?:Bearer )?)([\w\-]+)',
            _redact_match,
            env["HTTP_AUTHORIZATION"],
            re.ASCII,
        )

    print(repr(env))


def weasyl_exception_view(exc, request):
    """
    A view for general exceptions thrown by weasyl code.
    """
    # Avoid using the reified request.userid property here. It might not be set and it might
    # have changed due to signin/out.
    if hasattr(request, 'weasyl_session'):
        userid = request.userid
    else:
        userid = 0
        request.userid = 0  # To keep templates happy.
    errorpage_kwargs = {}
    if isinstance(exc, WeasylError):
        if exc.level is not None:
            _log_request(request)
            traceback.print_exception(exc, limit=1)
        status_code = errorcode.error_status_code.get(exc.value, 422)
        if exc.render_as_json:
            return Response(json={'error': {'name': exc.value}},
                            status_code=status_code)
        errorpage_kwargs = exc.errorpage_kwargs
        if exc.value in errorcode.error_messages:
            message = errorcode.error_messages[exc.value]
            if exc.error_suffix:
                message = '%s %s' % (message, exc.error_suffix)
            return Response(d.errorpage(userid, message, **errorpage_kwargs),
                            status_code=status_code)
    request_id = secrets.token_urlsafe(6)
    _log_request(request, request_id=request_id)
    traceback.print_exception(exc)
    if getattr(exc, "__render_as_json", False):
        return Response(json={'error': {}}, status_code=500)
    else:
        return Response(d.errorpage(userid, request_id=request_id, **errorpage_kwargs), status_code=500)


@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.perf_counter()


@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.perf_counter() - context._query_start_time
    request = get_current_request()  # TODO: There should be a better way to save this.
    if hasattr(request, 'sql_times'):
        request.sql_times.append(total)
    if hasattr(request, 'query_debug'):
        request.query_debug.append((statement, total))

import html
import re
import secrets
import time
import traceback
from datetime import datetime, timedelta, timezone

from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from sentry_sdk import capture_exception, push_scope, set_user
from sqlalchemy import event
from sqlalchemy.engine import Engine
from web.utils import storify

from libweasyl import staff
from libweasyl.cache import ThreadCacheProxy
from weasyl import define as d
from weasyl import errorcode
from weasyl import orm
from weasyl.error import WeasylError


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


def db_timer_tween_factory(handler, registry):
    """
    A tween that records timing information in the headers of a response.
    """
    def db_timer_tween(request):
        started_at = time.perf_counter()
        request.sql_times = []
        request.memcached_times = []
        resp = handler(request)
        ended_at = time.perf_counter()
        time_in_sql = sum(request.sql_times)
        time_in_memcached = sum(request.memcached_times)
        time_in_python = ended_at - started_at - time_in_sql - time_in_memcached
        resp.headers['X-SQL-Time-Spent'] = '%0.1fms' % (time_in_sql * 1000,)
        resp.headers['X-Memcached-Time-Spent'] = '%0.1fms' % (time_in_memcached * 1000,)
        resp.headers['X-Python-Time-Spent'] = '%0.1fms' % (time_in_python * 1000,)
        resp.headers['X-SQL-Queries'] = str(len(request.sql_times))
        resp.headers['X-Memcached-Queries'] = str(len(request.memcached_times))
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

        set_user(
            {"id": sess_obj.userid} if sess_obj
            else {"ip_address": request.client_addr})

        return handler(request)

    return session_tween


def query_debug_tween_factory(handler, registry):
    """
    A tween that allows developers to view timing per query.
    """
    def callback(request, response):
        if not hasattr(request, 'weasyl_session') or request.userid not in staff.DEVELOPERS:
            return

        class ParameterCounter(object):
            def __init__(self):
                self.next = 1
                self.ids = {}

            def __getitem__(self, name):
                id = self.ids.get(name)

                if id is None:
                    id = self.ids[name] = self.next
                    self.next += 1

                return u'$%i' % (id,)

        debug_rows = []

        for statement, t in request.query_debug:
            statement = u' '.join(statement.split()).replace(u'( ', u'(').replace(u' )', u')') % ParameterCounter()
            debug_rows.append(u'<tr><td>%.1f ms</td><td><code>%s</code></td></tr>' % (t * 1000, html.escape(statement)))

        response.text += u''.join(
            [u'<table style="background: white; border-collapse: separate; border-spacing: 1em; table-layout: auto; margin: 1em; font-family: sans-serif">']
            + debug_rows
            + [u'</table>']
        )

    def query_debug_tween(request):
        if 'query_debug' in request.params:
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


def _generate_http2_server_push_headers():
    """
    Generates the Link headers to load HTTP/2 Server Push resources which are needed on each pageload. Written
    as a separate function to only execute this code a single time, since we just need to generate this each
    time the code is relaunched (e.g., each time the web workers are kicked to a new version of the code).

    A component of ``http2_server_push_tween_factory``
    :return: An ASCII encoded string to be loaded into the Link header set inside of ``http2_server_push_tween_factory``
    """
    css_preload = [
        '<' + item + '>; rel=preload; as=style' for item in [
            d.get_resource_path('css/site.css'),
            d.get_resource_path('fonts/museo500.css'),
        ]
    ]

    js_preload = [
        '<' + item + '>; rel=preload; as=script' for item in [
            d.get_resource_path('js/jquery-2.2.4.min.js'),
            d.get_resource_path('js/scripts.js'),
        ]
    ]

    return ", ".join(css_preload + js_preload)


# Part of the `Link` header that will be set in the `http2_server_push_tween_factory` function, below
HTTP2_LINK_HEADER_PRELOADS = _generate_http2_server_push_headers()


def http2_server_push_tween_factory(handler, registry):
    """
    Add the 'Link' header to outgoing responses to HTTP/2 Server Push render-blocking resources
    """
    def http2_server_push(request):
        resp = handler(request)

        # Combined HTTP/2 headers indicating which resources to server push
        resp.headers['Link'] = HTTP2_LINK_HEADER_PRELOADS
        return resp
    return http2_server_push


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
        from weasyl.oauth2 import get_userid_from_authorization
        userid = get_userid_from_authorization(request)
        if not userid:
            raise HTTPUnauthorized(www_authenticate=('Bearer', 'realm="Weasyl" error="invalid_token"'))
        return userid

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
            capture_exception(exc, level=exc.level)
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
    with push_scope() as scope:
        scope.set_tag('request_id', request_id)
        event_id = capture_exception(exc)
    if event_id is not None:
        request_id = '%s-%s' % (event_id, request_id)
    print("unhandled error (request id %s) in %r" % (request_id, request.environ))
    traceback.print_exc()
    if getattr(exc, "__render_as_json", False):
        return Response(json={'error': {}}, status_code=500)
    else:
        return Response(d.errorpage(userid, request_id=request_id, **errorpage_kwargs), status_code=500)


def strip_session_cookie(event, hint):
    if request := event.get('request'):
        if (headers := request.get('headers')) and 'Cookie' in headers:
            headers['Cookie'] = re.sub(
                r'(WZL="?)([^";]+)',
                lambda match: match.group(1) + '*' * len(match.group(2)),
                headers['Cookie']
            )
        if (cookies := request.get('cookies')) and 'WZL' in cookies:
            cookies['WZL'] = '*' * len(cookies['WZL'])
    return event


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

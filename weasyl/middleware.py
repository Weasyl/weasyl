from __future__ import absolute_import

import os
import re
import sys
import time
import base64
import logging
import raven
import raven.processors
import traceback

from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from sqlalchemy import event
from sqlalchemy.engine import Engine
from twisted.internet.threads import blockingCallFromThread
from web.utils import storify

from libweasyl import security
from libweasyl.cache import ThreadCacheProxy
from weasyl import define as d
from weasyl import errorcode
from weasyl import http
from weasyl import orm
from weasyl.error import WeasylError


class ClientGoneAway(Exception):
    pass


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
        started_at = time.time()
        queued_at = request.environ.get('HTTP_X_REQUEST_STARTED_AT')
        if queued_at is None:
            return handler(request)

        request.sql_times = []
        request.memcached_times = []
        time_queued = started_at - float(queued_at)
        resp = handler(request)
        ended_at = time.time()
        time_in_sql = sum(request.sql_times)
        time_in_memcached = sum(request.memcached_times)
        time_in_python = ended_at - started_at - time_in_sql - time_in_memcached
        resp.headers['X-Queued-Time-Spent'] = '%0.1fms' % (time_queued * 1000,)
        resp.headers['X-SQL-Time-Spent'] = '%0.1fms' % (time_in_sql * 1000,)
        resp.headers['X-Memcached-Time-Spent'] = '%0.1fms' % (time_in_memcached * 1000,)
        resp.headers['X-Python-Time-Spent'] = '%0.1fms' % (time_in_python * 1000,)
        resp.headers['X-SQL-Queries'] = str(len(request.sql_times))
        resp.headers['X-Memcached-Queries'] = str(len(request.memcached_times))
        sess = request.weasyl_session
        d.statsFactory.logRequest(
            time_queued, time_in_sql, time_in_memcached, time_in_python,
            len(request.sql_times), len(request.memcached_times),
            sess.userid, sess.sessionid, request.method, request.path,
            request.query_string.split(','))
        return resp
    return db_timer_tween


def session_tween_factory(handler, registry):
    """
    A tween that sets a weasyl_session on a request.
    """
    # TODO(hyena): Investigate a pyramid session_factory implementation instead.
    def session_tween(request):
        cookies_to_clear = set()
        if 'beaker.session.id' in request.cookies:
            cookies_to_clear.add('beaker.session.id')

        session = d.connect()
        sess_obj = None
        if 'WZL' in request.cookies:
            sess_obj = session.query(orm.Session).get(request.cookies['WZL'])
            if sess_obj is None:
                # clear an invalid session cookie if nothing ends up trying to create a
                # new one
                cookies_to_clear.add('WZL')

        if sess_obj is None:
            sess_obj = orm.Session()
            sess_obj.create = True
            sess_obj.sessionid = security.generate_key(64)
        # BUG: Because of the way our exception handler relies on a weasyl_session, exceptions
        # thrown before this part will not be handled correctly.
        request.weasyl_session = sess_obj

        # Register a response callback to clear and set the session cookies before returning.
        # Note that this requires that exceptions are handled properly by our exception view.
        def callback(request, response):
            if sess_obj.save:
                session.begin()
                if sess_obj.create:
                    session.add(sess_obj)
                    response.set_cookie('WZL', sess_obj.sessionid, max_age=60 * 60 * 24 * 365,
                                        secure=request.scheme == 'https', httponly=True)
                    # don't try to clear the cookie if we're saving it
                    cookies_to_clear.discard('WZL')
                session.commit()
            for name in cookies_to_clear:
                response.delete_cookie(name)

        request.add_response_callback(callback)
        return handler(request)

    return session_tween


def status_check_tween_factory(handler, registry):
    """
    A tween that checks if the weasyl user is banned, suspended, etc. and redirects appropriately.

    Rather than performing these checks on every view.
    """
    def status_check_tween(request):
        status = d.common_status_check(request.userid)
        if status:
            return Response(d.common_status_page(request.userid, status))
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
            '/static/fonts/museo500.css',
        ]
    ]

    js_preload = [
        '<' + item + '>; rel=preload; as=script' for item in [
            '/static/jquery-2.2.4.min.js',
            '/static/typeahead.bundle.min.js',
            '/static/marked.js?' + d.CURRENT_SHA,
            '/static/scripts.js?' + d.CURRENT_SHA,
        ]
    ]

    return ", ".join(css_preload + js_preload).encode('ascii')


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
        userid = request.weasyl_session.userid
        return 0 if userid is None else userid


def log_exc_request_method(request, **kwargs):
    """
    Method on requests to log exceptions.
    """
    # It's unclear to me why this should be a request method and not just define.log_exc().
    return request.environ.get('raven.captureException', lambda **kw: traceback.print_exc())(**kwargs)


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


# Methods to add response callbacks to a request. The callbacks run in the order they
# were registered. Note that these will not run if an exception is thrown that isn't handled by
# our exception view.
def set_cookie_on_response(request, name=None, value='', max_age=None, path='/', domain=None,
                           secure=False, httponly=False, comment=None, overwrite=False):
    """
    Registers a callback on the request to set a cookie in the response.
    Parameters have the same meaning as ``pyramid.response.Response.set_cookie``.
    """
    def callback(request, response):
        response.set_cookie(name, value, max_age, path, domain, secure, httponly, comment,
                            overwrite)
    request.add_response_callback(callback)


def delete_cookie_on_response(request, name, path='/', domain=None):
    """
    Register a callback on the request to delete a cookie from the client.
    Parameters have the same meaning as ``pyramid.response.Response.delete_cookie``.
    """
    def callback(request, response):
        response.delete_cookie(name, path, domain)
    request.add_response_callback(callback)


def weasyl_exception_view(exc, request):
    """
    A view for general exceptions thrown by weasyl code.
    """
    if isinstance(exc, ClientGoneAway):
        if 'raven.captureMessage' in request.environ:
            request.environ['raven.captureMessage']('HTTP client went away', level=logging.INFO)
        return request.response
    else:
        # Avoid using the reified request.userid property here. It might not be set and it might
        # have changed due to signin/out.
        if hasattr(request, 'weasyl_session'):
            userid = request.weasyl_session.userid
        else:
            userid = 0
            request.userid = 0  # To keep templates happy.
        errorpage_kwargs = {}
        if isinstance(exc, WeasylError):
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
        request_id = None
        if 'raven.captureException' in request.environ:
            request_id = base64.b64encode(os.urandom(6), '+-')
            event_id = request.environ['raven.captureException'](request_id=request_id)
            request_id = '%s-%s' % (event_id, request_id)
        print "unhandled error (request id %s) in %r" % (request_id, request.environ)
        traceback.print_exc()
        if getattr(exc, "__render_as_json", False):
            return Response(json={'error': {}}, status_code=500)
        else:
            return Response(d.errorpage(userid, request_id=request_id, **errorpage_kwargs), status_code=500)


class RemoveSessionCookieProcessor(raven.processors.Processor):
    """
    Removes Weasyl session cookies.
    """
    def _filter_header(self, value):
        return re.sub(
            r'WZL=(\w+)',
            lambda match: 'WZL=' + '*' * len(match.group(1)),
            value)

    def filter_http(self, data):
        if 'cookies' in data:
            data['cookies'] = self._filter_header(data['cookies'])

        if 'headers' in data and 'Cookie' in data['headers']:
            data['headers']['Cookie'] = self._filter_header(data['headers']['Cookie'])

        if 'env' in data and 'HTTP_COOKIE' in data['env']:
            data['env']['HTTP_COOKIE'] = self._filter_header(data['env']['HTTP_COOKIE'])


class URLSchemeFixingMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PROTO') == 'https':
            environ['wsgi.url_scheme'] = 'https'
        return self.app(environ, start_response)


class SentryEnvironmentMiddleware(object):
    def __init__(self, app, dsn, reactor=None):
        self.app = app
        self.client = raven.Client(
            dsn=dsn,
            release=d.CURRENT_SHA,
            processors=[
                'raven.processors.SanitizePasswordsProcessor',
                'weasyl.middleware.RemoveSessionCookieProcessor',
            ],
        )
        if reactor is None:
            from twisted.internet import reactor
        self.reactor = reactor

    def ravenCaptureArguments(self, level=None, **extra):
        request = get_current_request()
        data = {
            'level': level,
            'user': {
                'id': d.get_userid(),
                'ip_address': d.get_address(),
            },
            'request': {
                'url': request.environ['PATH_INFO'],
                'method': request.environ['REQUEST_METHOD'],
                'data': request.POST,
                'query_string': request.environ['QUERY_STRING'],
                'headers': http.get_headers(request.environ),
                'env': request.environ,
            },
        }

        return {
            'data': data,
            'extra': dict(
                extra,
                session=getattr(request, 'weasyl_session', None),
            ),
        }

    def captureException(self, **extra):
        kwargs = self.ravenCaptureArguments(**extra)
        exc_info = sys.exc_info()
        return blockingCallFromThread(
            self.reactor, self.client.captureException, exc_info, **kwargs)

    def captureMessage(self, message, **extra):
        kwargs = self.ravenCaptureArguments(**extra)
        return blockingCallFromThread(
            self.reactor, self.client.captureMessage, message, **kwargs)

    def __call__(self, environ, start_response):
        environ['raven.captureException'] = self.captureException
        environ['raven.captureMessage'] = self.captureMessage
        return self.app(environ, start_response)


def _wrapperfunc(name):
    def wrap(self, *a, **kw):
        meth = getattr(self._wrapped, name)
        try:
            return meth(*a, **kw)
        except ValueError:
            raise ClientGoneAway()
    return wrap


class InputWrap(object):
    def __init__(self, wrapped):
        self._wrapped = wrapped

    read = _wrapperfunc('read')
    readline = _wrapperfunc('readline')
    readlines = _wrapperfunc('readlines')

    def __iter__(self):
        it = iter(self._wrapped)
        while True:
            try:
                yield next(it)
            except StopIteration:
                return
            except ValueError:
                raise ClientGoneAway()


class InputWrapMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['wsgi.input'] = InputWrap(environ['wsgi.input'])
        return self.app(environ, start_response)


@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()


@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    request = get_current_request()  # TODO: There should be a better way to save this.
    if hasattr(request, 'sql_times'):
        request.sql_times.append(total)

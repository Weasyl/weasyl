import os
import re
import sys
import time
import base64
import logging
import raven
import raven.processors
import traceback

import anyjson as json
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from sqlalchemy import event
from sqlalchemy.engine import Engine
from twisted.internet.threads import blockingCallFromThread

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


def property_tween_factory(handler, registry):
    """
    A tween to set up the some properties on a request.

    We do this in a tween so other tweens can use it before it hits the weasyl WSGI.
    """
    def property_tween(request):
        # Set up the db connection property.
        # TODO(strain-113): Should we set this up as part of the WSGI environment?
        request.set_property(d.pg_connection_callable, 'pg_connection', reify=True)
        # Set up the exception logger. Since this is inexpensive we just make it an attribute.
        request.log_exc = request.environ.get(
            'raven.captureException', lambda **kw: traceback.print_exc())
        return handler(request)
    return property_tween


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

    TODO(strain-113): This should be replaced with a real pyramid session_factory implementation.
    """
    def session_tween(request):
        cookies = request.cookies
        cookies_to_clear = set()
        if 'beaker.session.id' in cookies:
            cookies_to_clear.add('beaker.session.id')

        session = d.connect()
        sess_obj = None
        if 'WZL' in cookies:
            sess_obj = session.query(orm.Session).get(cookies['WZL'])
            if sess_obj is None:
                # clear an invalid session cookie if nothing ends up trying to create a
                # new one
                cookies_to_clear.add('WZL')

        if sess_obj is None:
            sess_obj = orm.Session()
            sess_obj.create = True
            sess_obj.sessionid = security.generate_key(64)
        request.weasyl_session = sess_obj

        try:
            resp = handler(request)
            return resp
        finally:
            if resp is None:
                resp = request.response
            if sess_obj.save:
                session.begin()
                if sess_obj.create:
                    session.add(sess_obj)
                    # TODO(strain-113): Does this need https considerations?
                    resp.set_cookie('WZL', sess_obj.sessionid, max_age=60 * 60 * 24 * 365)
                    # don't try to clear the cookie if we're saving it
                    cookies_to_clear.discard('WZL')
                session.commit()

            for name in cookies_to_clear:
                resp.delete_cookie(name)
    return session_tween


def weasyl_exception_view(exc, request):
    """
    A view for general exceptions thrown by weasyl code.
    """

    # TODO: This flow control is a bit of an anti-pattern.
    if isinstance(exc, ClientGoneAway):
        if 'raven.captureMessage' in request.environ:
            request.environ['raven.captureMessage']('HTTP client went away', level=logging.INFO)
        return Response()
    else:
        userid = d.get_userid()
        errorpage_kwargs = {}
        if isinstance(exc, WeasylError):
            if exc.render_as_json:
                # Should this use an error code?
                return Response(json.dumps({'error': {'name': exc.value}}))
            errorpage_kwargs = exc.errorpage_kwargs
            if exc.value in errorcode.error_messages:
                # This is wrong:
                status_info = errorcode.error_status_code.get(exc.value, (200, "200 OK",))
                message = '%s %s' % (errorcode.error_messages[exc.value], exc.error_suffix)
                return Response(d.errorpage(userid, message, **errorpage_kwargs),
                                status_int=status_info[0],
                                status=status_info[1])
        request_id = None
        if 'raven.captureException' in request.environ:
            request_id = base64.b64encode(os.urandom(6), '+-')
            event_id = request.environ['raven.captureException'](request_id=request_id)
            request_id = '%s-%s' % (event_id, request_id)
        print "unhandled error (request id %s) in %r" % (request_id, request.environ)
        traceback.print_exc()
        if getattr(exc, "__render_as_json", False):
            body = json.dumps({'error': {}})
        else:
            body = d.errorpage(userid, request_id=request_id, **errorpage_kwargs)
        return Response(body, status_int=500, status="500 Internal Server Error")


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
                session=request.get('weasyl_session'),
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

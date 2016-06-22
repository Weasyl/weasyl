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
from sqlalchemy import event
from sqlalchemy.engine import Engine
from twisted.internet.threads import blockingCallFromThread
import web
import web.webapi

from libweasyl import security
from libweasyl.cache import ThreadCacheProxy
from weasyl import define as d
from weasyl import errorcode
from weasyl import orm
from weasyl.error import WeasylError


def _get_headers(env):
    return {
        key[5:].replace('_', '-').title(): value
        for key, value in env.iteritems() if key.startswith('HTTP_')}


class ClientGoneAway(Exception):
    pass


def db_connection_processor(handle):
    try:
        return handle()
    finally:
        if 'pg_connection' in web.ctx:
            web.ctx.pg_connection.close()


def session_processor(handle):
    cookies = web.cookies()
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
    web.ctx.weasyl_session = sess_obj

    try:
        return handle()
    finally:
        if sess_obj.save:
            session.begin()
            if sess_obj.create:
                session.add(sess_obj)
                web.setcookie('WZL', sess_obj.sessionid, expires=60 * 60 * 24 * 365,
                              secure=web.ctx.protocol == 'https', httponly=True)
                # don't try to clear the cookie if we're saving it
                cookies_to_clear.discard('WZL')
            session.commit()

        for name in cookies_to_clear:
            # this sets the cookie to expire one second before the HTTP request was
            # issued, which is the closest you can get to 'clearing' a cookie.
            web.setcookie(name, '', expires=-1)


# this gets set by weasyl.py to the web.py application handler. it's global
# mutable state, but this is application code so I can't bring myself to care
# at the moment. maybe refactor later if necessary.
_handle = None


def weasyl_exception_processor():
    web.ctx.log_exc = web.ctx.env.get(
        'raven.captureException', lambda **kw: traceback.print_exc())
    try:
        return _handle()
    except ClientGoneAway:
        if 'raven.captureMessage' in web.ctx.env:
            web.ctx.env['raven.captureMessage']('HTTP client went away', level=logging.INFO)
        return ''
    except web.HTTPError:
        raise
    except Exception as e:
        userid = d.get_userid()
        errorpage_kwargs = {}
        if isinstance(e, WeasylError):
            if e.render_as_json:
                return json.dumps({'error': {'name': e.value}})
            errorpage_kwargs = e.errorpage_kwargs
            if e.value in errorcode.error_messages:
                web.ctx.status = errorcode.error_status_code.get(e.value, '200 OK')
                message = '%s %s' % (errorcode.error_messages[e.value], e.error_suffix)
                return d.errorpage(userid, message, **errorpage_kwargs)
        web.ctx.status = '500 Internal Server Error'
        request_id = None
        if 'raven.captureException' in web.ctx.env:
            request_id = base64.b64encode(os.urandom(6), '+-')
            event_id = web.ctx.env['raven.captureException'](request_id=request_id)
            request_id = '%s-%s' % (event_id, request_id)
        print 'unhandled error (request id %s) in %r' % (request_id, web.ctx.env)
        traceback.print_exc()
        if getattr(e, '__render_as_json', False):
            return json.dumps({'error': {}})
        return d.errorpage(userid, request_id=request_id, **errorpage_kwargs)


_delegate = None


def endpoint_recording_delegate(f, fvars, args=()):
    web.ctx.endpoint = f, args
    return _delegate(f, fvars, args)


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
        data = {
            'level': level,
            'user': {
                'id': d.get_userid(),
                'ip_address': d.get_address(),
            },
            'request': {
                'url': web.ctx.env['PATH_INFO'],
                'method': web.ctx.env['REQUEST_METHOD'],
                'data': web.webapi.rawinput(method='POST'),
                'query_string': web.ctx.env['QUERY_STRING'],
                'headers': _get_headers(web.ctx.env),
                'env': web.ctx.env,
            },
        }

        return {
            'data': data,
            'extra': dict(
                extra,
                session=web.ctx.get('weasyl_session'),
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
    if hasattr(web.ctx, 'sql_times'):
        web.ctx.sql_times.append(total)


def db_timer_processor(app):
    def processor(handle):
        started_at = time.time()
        queued_at = web.ctx.env.get('HTTP_X_REQUEST_STARTED_AT')
        if queued_at is None:
            return handle()

        web.ctx.sql_times = []
        web.ctx.memcached_times = []
        time_queued = started_at - float(queued_at)
        ret = handle()
        ended_at = time.time()
        time_in_sql = sum(web.ctx.sql_times)
        time_in_memcached = sum(web.ctx.memcached_times)
        time_in_python = ended_at - started_at - time_in_sql - time_in_memcached
        web.header('X-Queued-Time-Spent', '%0.1fms' % (time_queued * 1000,))
        web.header('X-SQL-Time-Spent', '%0.1fms' % (time_in_sql * 1000,))
        web.header('X-Memcached-Time-Spent', '%0.1fms' % (time_in_memcached * 1000,))
        web.header('X-Python-Time-Spent', '%0.1fms' % (time_in_python * 1000,))
        web.header('X-SQL-Queries', str(len(web.ctx.sql_times)))
        web.header('X-Memcached-Queries', str(len(web.ctx.memcached_times)))
        sess = web.ctx.weasyl_session
        app.statsFactory.logRequest(
            time_queued, time_in_sql, time_in_memcached, time_in_python,
            len(web.ctx.sql_times), len(web.ctx.memcached_times),
            sess.userid, sess.sessionid, web.ctx.method, *web.ctx.endpoint)
        return ret

    return processor


def cache_clear_processor(handle):
    try:
        return handle()
    finally:
        ThreadCacheProxy.zap_cache()

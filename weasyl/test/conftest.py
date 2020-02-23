# pytest configuration for weasyl db test fixture.
# The filename conftest.py is magical, do not change.

from __future__ import absolute_import

import errno
import json
import os
import shutil

import pytest
import pyramid.testing
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.dialects.postgresql import psycopg2
from webtest import TestApp

from weasyl import config
config._in_test = True  # noqa

from libweasyl import cache
from libweasyl.cache import JSONProxy, ThreadCacheProxy
from libweasyl.configuration import configure_libweasyl
from libweasyl.models.tables import metadata
from weasyl import (
    commishinfo,
    define,
    emailer,
    macro,
    media,
    middleware,
    spam_filtering,
)
from weasyl.controllers.routes import setup_routes_and_views
from weasyl.wsgi import wsgi_app, setup_jinja2_env


cache.region.configure(
    'dogpile.cache.memory',
    wrap=[ThreadCacheProxy, JSONProxy],
)
define.metric = lambda *a, **kw: None


configure_libweasyl(
    dbsession=define.sessionmaker,
    not_found_exception=HTTPNotFound,
    base_file_path=macro.MACRO_STORAGE_ROOT,
    staff_config_dict={},
    media_link_formatter_callback=media.format_media_link,
)


@pytest.fixture(scope='session', autouse=True)
def setupdb(request):
    define.engine.execute('DROP SCHEMA public CASCADE')
    define.engine.execute('CREATE SCHEMA public')
    define.engine.execute('CREATE EXTENSION HSTORE')
    define.engine.execute('CREATE EXTENSION FUZZYSTRMATCH')

    # hstore oids changed; de-memoize them and create new connections
    define.engine.dialect._hstore_oids = psycopg2.PGDialect_psycopg2._hstore_oids.__get__(define.engine.dialect)
    define.engine.dispose()

    define.meta.create_all(define.engine)


@pytest.yield_fixture(autouse=True)
def empty_storage():
    try:
        os.mkdir(macro.MACRO_STORAGE_ROOT)
    except OSError as e:
        if e.errno == errno.EEXIST:
            raise Exception("Storage directory should not exist when running tests")

        raise

    os.mkdir(macro.MACRO_SYS_LOG_PATH)
    os.mkdir(os.path.join(macro.MACRO_STORAGE_ROOT, 'static'))
    os.mkdir(os.path.join(macro.MACRO_STORAGE_ROOT, 'static', 'media'))
    os.symlink('ad', os.path.join(macro.MACRO_STORAGE_ROOT, 'static', 'media', 'ax'))

    try:
        yield
    finally:
        shutil.rmtree(macro.MACRO_STORAGE_ROOT)


@pytest.fixture(autouse=True)
def setup_request_environment(request):
    pyramid_request = pyramid.testing.DummyRequest()
    pyramid_request.set_property(middleware.pg_connection_request_property, name='pg_connection', reify=True)
    pyramid_request.set_property(middleware.userid_request_property, name='userid', reify=True)
    pyramid_request.log_exc = middleware.log_exc_request_method
    pyramid_request.web_input = middleware.web_input_request_method
    pyramid_request.environ['HTTP_X_FORWARDED_FOR'] = '127.0.0.1'
    pyramid_request.client_addr = '127.0.0.1'
    config = pyramid.testing.setUp(request=pyramid_request)
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('weasyl:templates/', name='.jinja2')
    config.action(None, setup_jinja2_env, order=999)
    setup_routes_and_views(config)

    def tear_down():
        pyramid_request.pg_connection.close()
        pyramid.testing.tearDown()

    request.addfinalizer(tear_down)


@pytest.fixture(autouse=True)
def lower_bcrypt_rounds(monkeypatch):
    monkeypatch.setattr(macro, 'MACRO_BCRYPT_ROUNDS', 4)


@pytest.fixture(autouse=True)
def drop_email(monkeypatch):
    def drop_send(mailto, subject, content):
        pass

    monkeypatch.setattr(emailer, 'send', drop_send)


@pytest.fixture
def db(request):
    db = define.connect()

    def tear_down():
        """ Clears all rows from the test database. """
        db.flush()
        for table in metadata.tables.values():
            db.execute(table.delete())

    request.addfinalizer(tear_down)

    if request.cls is not None:
        request.cls.db = db

    return db


@pytest.fixture(name='cache')
def cache_(request):
    cache.region.configure(
        'dogpile.cache.memory',
        wrap=[ThreadCacheProxy, JSONProxy],
        replace_existing_backend=True,
    )


@pytest.fixture
def no_csrf(monkeypatch):
    monkeypatch.setattr(define, 'is_csrf_valid', lambda request, token: True)


@pytest.fixture(autouse=True)
def deterministic_marketplace_tests(monkeypatch):
    rates = """{"base":"USD","date":"2017-04-03","rates":{"AUD":1.3143,"BGN":1.8345,"BRL":3.1248,"CAD":1.3347,"CHF":1.002,"CNY":6.8871,"CZK":25.367,"DKK":6.9763,"GBP":0.79974,"HKD":7.7721,"HRK":6.9698,"HUF":289.54,"IDR":13322.0,"ILS":3.6291,"INR":64.985,"JPY":111.28,"KRW":1117.2,"MXN":18.74,"MYR":4.4275,"NOK":8.5797,"NZD":1.4282,"PHP":50.142,"PLN":3.9658,"RON":4.2674,"RUB":56.355,"SEK":8.9246,"SGD":1.3975,"THB":34.385,"TRY":3.6423,"ZAR":13.555,"EUR":0.938}}"""

    def _fetch_rates():
        return json.loads(rates)

    monkeypatch.setattr(commishinfo, '_fetch_rates', _fetch_rates)


@pytest.fixture
def app():
    return TestApp(wsgi_app, extra_environ={'HTTP_X_FORWARDED_FOR': '::1'})


@pytest.fixture(autouse=True)
def do_not_run_spam_checks(monkeypatch):
    monkeypatch.setattr(spam_filtering, 'FILTERING_ENABLED', False)

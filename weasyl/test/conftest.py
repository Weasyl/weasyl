# pytest configuration for weasyl db test fixture.
# The filename conftest.py is magical, do not change.

import errno
import json
import os
import shutil

import pytest
import pyramid.testing
from pytest import MonkeyPatch
from webtest import TestApp as TestApp_

from weasyl import config
config._in_test = True

from libweasyl.cache import region
from libweasyl.configuration import configure_libweasyl
from libweasyl.staff import StaffConfig
from libweasyl.test.common import cache_backend
from libweasyl.test.common import clear_database
from weasyl import (
    commishinfo,
    define,
    emailer,
    macro,
    media,
    middleware,
    turnstile,
)
from weasyl.controllers.routes import setup_routes_and_views
from weasyl.test.common import initialize_database
from weasyl.wsgi import make_wsgi_app


@pytest.fixture(scope="session", autouse=True)
def configure_libweasyl_():
    configure_libweasyl(
        dbsession=define.sessionmaker,
        base_file_path=macro.MACRO_STORAGE_ROOT,
        staff_config=StaffConfig(),
        media_link_formatter_callback=media.format_media_link,
    )


@pytest.fixture(scope='session', autouse=True)
def setupdb():
    define.engine.execute(
        "DROP SCHEMA public CASCADE;"
        "CREATE SCHEMA public;"
    )

    define.meta.create_all(define.engine)


@pytest.fixture(autouse=True)
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

    yield

    shutil.rmtree(macro.MACRO_STORAGE_ROOT)


@pytest.fixture(scope="session")
def configurator():
    config = pyramid.testing.setUp()
    setup_routes_and_views(config)

    yield config

    pyramid.testing.tearDown()


@pytest.fixture(autouse=True)
def setup_request_environment(configurator):
    pyramid_request = pyramid.testing.DummyRequest()
    pyramid_request.set_property(middleware.pg_connection_request_property, name='pg_connection', reify=True)
    pyramid_request.set_property(middleware.userid_request_property, name='userid', reify=True)
    pyramid_request.web_input = middleware.web_input_request_method
    pyramid_request.environ['HTTP_X_FORWARDED_FOR'] = '127.0.0.1'
    pyramid_request.client_addr = '127.0.0.1'
    configurator.begin(request=pyramid_request)

    yield

    pyramid_request.pg_connection.close()


@pytest.fixture(scope="session", autouse=True)
def lower_bcrypt_rounds():
    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(macro, 'MACRO_BCRYPT_ROUNDS', 4)
        yield


@pytest.fixture(scope="session", autouse=True)
def drop_email():
    def drop_send(mailto, subject, content):
        pass

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(emailer, 'send', drop_send)
        yield


@pytest.fixture
def db():
    initialize_database(define.engine)
    yield define.get_current_request().pg_connection
    clear_database(define.engine)


@pytest.fixture
def cache():
    region.backend.zap_cache()
    try:
        yield
    finally:
        region.backend.zap_cache()


@pytest.fixture(scope="session", autouse=True)
def localhost_origin():
    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(define, "ORIGIN", "http://localhost")
        yield


@pytest.fixture(scope="session", autouse=True)
def deterministic_marketplace_tests():
    rates = """{"base":"USD","date":"2017-04-03","rates":{"AUD":1.3143,"BGN":1.8345,"BRL":3.1248,"CAD":1.3347,"CHF":1.002,"CNY":6.8871,"CZK":25.367,"DKK":6.9763,"GBP":0.79974,"HKD":7.7721,"HRK":6.9698,"HUF":289.54,"IDR":13322.0,"ILS":3.6291,"INR":64.985,"JPY":111.28,"KRW":1117.2,"MXN":18.74,"MYR":4.4275,"NOK":8.5797,"NZD":1.4282,"PHP":50.142,"PLN":3.9658,"RON":4.2674,"RUB":56.355,"SEK":8.9246,"SGD":1.3975,"THB":34.385,"TRY":3.6423,"ZAR":13.555,"EUR":0.938}}"""

    def _fetch_rates():
        return json.loads(rates)

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(commishinfo, '_fetch_rates', _fetch_rates)
        yield


@pytest.fixture(scope="session", autouse=True)
def disable_turnstile():
    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(turnstile, "SITE_KEY", None)
        yield


@pytest.fixture(scope='session')
def wsgi_app():
    return make_wsgi_app(configure_cache=False)


class TestApp(TestApp_):

    def do_request(self, req, status=None, expect_errors=None):
        if 'wsgi.input' in req.environ:
            req.environ['wsgi.input_terminated'] = True
        if req.method in ["POST", "DELETE", "PUT", "PATCH"]:
            req.headers.setdefault("Origin", "http://localhost")
        return super().do_request(req, status, expect_errors)


@pytest.fixture()
def app(wsgi_app):
    return TestApp(wsgi_app, extra_environ={'HTTP_X_FORWARDED_FOR': '::1'})


__all__ = [
    "cache_backend",
    "configure_libweasyl_",
    "setupdb",
    "empty_storage",
    "configurator",
    "setup_request_environment",
    "lower_bcrypt_rounds",
    "drop_email",
    "db",
    "cache",
    "localhost_origin",
    "deterministic_marketplace_tests",
    "disable_turnstile",
    "wsgi_app",
    "app",
]

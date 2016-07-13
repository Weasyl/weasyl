# pytest configuration for weasyl db test fixture.
# The filename conftest.py is magical, do not change.

import pytest
import web

from weasyl import config
config._in_test = True  # noqa

from libweasyl.configuration import configure_libweasyl
from libweasyl.models.tables import metadata
from weasyl import cache, define, emailer, macro, media
cache.region.configure('dogpile.cache.memory')
define.metric = lambda *a, **kw: None


configure_libweasyl(
    dbsession=define.sessionmaker,
    not_found_exception=web.notfound,
    base_file_path='testing',
    staff_config_dict={},
    media_link_formatter_callback=media.format_media_link,
)


@pytest.fixture(scope='session', autouse=True)
def setupdb(request):
    db = define.connect()
    db.execute('DROP SCHEMA public CASCADE')
    db.execute('CREATE SCHEMA public')
    db.execute('CREATE EXTENSION HSTORE')
    define.meta.create_all(define.engine)


@pytest.fixture(autouse=True)
def setup_request_environment():
    web.ctx.env = {'HTTP_X_FORWARDED_FOR': '127.0.0.1'}
    web.ctx.ip = '127.0.0.1'


@pytest.fixture(autouse=True)
def lower_bcrypt_rounds(monkeypatch):
    monkeypatch.setattr(macro, 'MACRO_BCRYPT_ROUNDS', 4)


@pytest.fixture(autouse=True)
def drop_email(monkeypatch):
    def drop_append(mailto, mailfrom, subject, content, displayto=None):
        pass

    monkeypatch.setattr(emailer, 'append', drop_append)


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

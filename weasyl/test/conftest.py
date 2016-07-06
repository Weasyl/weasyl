# pytest configuration for weasyl db test fixture.
# The filename conftest.py is magical, do not change.

import pytest
import web

from weasyl import config
config._in_test = True  # noqa

from libweasyl.configuration import configure_libweasyl
from libweasyl.models.meta import registry
from weasyl import cache, define, media
cache.region.configure('dogpile.cache.memory')
define.metric = lambda *a, **kw: None

staff_dict = {
        'directors': [],
        'technical_staff': [],
        'admins': [],
        'mods': [],
        'developers': [],
    }
configure_libweasyl(
    dbsession=define.sessionmaker,
    not_found_exception=web.notfound,
    base_file_path='testing',
    staff_config_dict=staff_dict,
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


@pytest.fixture
def db(request):
    db = define.connect()

    def tear_down():
        """ Clears all rows from the test database. """
        for k, cls in registry.iteritems():
            if not k[0].isupper():
                continue
            db.query(cls).delete()
        db.flush()

    request.addfinalizer(tear_down)
    return db

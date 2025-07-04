import os

import pytest
import sqlalchemy as sa

from libweasyl.configuration import configure_libweasyl
from libweasyl.models.meta import registry
from libweasyl.models.tables import metadata
from libweasyl.staff import StaffConfig
from libweasyl.test.common import dummy_format_media_link
from libweasyl import cache


engine = sa.create_engine(
    os.environ.get('WEASYL_TEST_SQLALCHEMY_URL', 'postgresql+psycopg2:///weasyl_test'),
    connect_args={
        'options': '-c TimeZone=UTC',
    },
)
sessionmaker = sa.orm.scoped_session(sa.orm.sessionmaker(bind=engine))


@pytest.fixture(scope='session', autouse=True)
def setup(request):
    db = sessionmaker()
    db.execute('DROP SCHEMA public CASCADE')
    db.execute('CREATE SCHEMA public')
    db.execute('CREATE EXTENSION HSTORE')
    db.commit()
    metadata.create_all(engine)

    cache.region.configure(
        'dogpile.cache.memory',
        wrap=[cache.ThreadCacheProxy],
    )


@pytest.fixture(autouse=True)
def staticdir(tmpdir):
    tmpdir = tmpdir.join('libweasyl-staticdir')
    configure_libweasyl(
        dbsession=sessionmaker,
        base_file_path=tmpdir.strpath,
        staff_config=StaffConfig(),
        media_link_formatter_callback=dummy_format_media_link,
    )
    return tmpdir


@pytest.fixture
def db(request):
    db = sessionmaker()
    # If a previous test has failed due to an SQL problem, the session will be
    # in a broken state, requiring a rollback. It's not harmful to
    # unconditionally rollback, so just do that.
    db.rollback()

    def tear_down():
        "Clears all rows from the test database."
        for k, cls in registry.items():
            if not k[0].isupper():
                continue
            db.query(cls).delete()
        db.flush()
        db.commit()

    request.addfinalizer(tear_down)
    return db

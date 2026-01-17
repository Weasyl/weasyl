import os

import pytest
import sqlalchemy as sa

from libweasyl.configuration import configure_libweasyl
from libweasyl.models.tables import metadata
from libweasyl.staff import StaffConfig
from libweasyl.test.common import clear_database
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
def setup():
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
def staticdir(tmp_path):
    storage_root = tmp_path / 'libweasyl-staticdir'
    storage_root.mkdir()
    configure_libweasyl(
        dbsession=sessionmaker,
        base_file_path=str(storage_root),
        staff_config=StaffConfig(),
        media_link_formatter_callback=dummy_format_media_link,
    )
    return storage_root


@pytest.fixture
def db():
    with sessionmaker() as db:
        yield db

    clear_database(engine)

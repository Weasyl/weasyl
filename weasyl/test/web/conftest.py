import pytest

from weasyl.test import db_utils


@pytest.fixture
def submission_user(db, cache):
    return db_utils.create_user(username='submission_test')

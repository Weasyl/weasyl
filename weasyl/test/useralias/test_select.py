import pytest

from weasyl.test import db_utils
from weasyl import useralias
from weasyl import define as d


test_alias = "testalias"


@pytest.mark.usefixtures('db')
def test_selecting_alias_succeeds():
    # This is the default case
    user_id = db_utils.create_user()
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    query = useralias.select(userid=user_id)
    # The manually set alias should equal what the function returns.
    assert test_alias == query


@pytest.mark.usefixtures('db')
def test_selecting_alias_when_user_has_no_alias_returns_zero_length_array():
    user_id = db_utils.create_user()
    queried_user_alias = useralias.select(userid=user_id)
    # Result when user has no alias set: should be None
    assert queried_user_alias is None

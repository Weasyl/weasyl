from weasyl.test import db_utils
from weasyl import useralias
from weasyl import define as d


def test_selecting_alias_succeeds_if_premium_parameter_is_set_to_true():
    # This is the default case
    user_id = db_utils.create_user()
    test_alias = "testalias0001"
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    query = useralias.select(userid=user_id, premium=True)
    # The manually set alias should equal what the function returns.
    assert test_alias == query


def test_selecting_alias_succeeds_if_premium_parameter_is_set_to_false():
    user_id = db_utils.create_user()
    test_alias = "testalias0002"
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    # The manually set alias should equal what the function returns.
    assert test_alias == queried_user_alias


def test_selecting_alias_when_user_has_no_alias_returns_zero_length_array_if_premium_parameter_is_set_to_true():
    user_id = db_utils.create_user()
    queried_user_alias = useralias.select(userid=user_id, premium=True)
    # Result when user has no alias set: should be a list, and be zero-length
    assert queried_user_alias == []


def test_selecting_alias_when_user_has_no_alias_returns_zero_length_array_if_premium_parameter_is_set_to_false():
    user_id = db_utils.create_user()
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    # Result when user has no alias set: should be a list, and be zero-length
    assert queried_user_alias == []

import pytest

from weasyl.test import db_utils
from weasyl import useralias
from weasyl import define as d
from weasyl.error import WeasylError


def test_setting_alias_fails_if_target_alias_exists():
    user_id = db_utils.create_user(username="testalias003")
    user_id_existing = db_utils.create_user(username="testalias004")
    test_alias_existing = "testalias005"
    test_alias = test_alias_existing
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id_existing, alias=test_alias_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' == err.value.value


def test_setting_alias_fails_if_target_username_exists():
    user_name = "testalias006"
    user_name_existing = "testalias007"
    test_alias = user_name_existing
    user_id = db_utils.create_user(username=user_name)
    db_utils.create_user(username=user_name_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' == err.value.value


def test_setting_alias_fails_if_user_does_not_have_premium_status():
    user_name = "testalias008"
    user_id = db_utils.create_user(username=user_name)
    user_alias = "testalias009"
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, user_alias)
    assert 'InsufficientPermissions' == err.value.value


def test_setting_alias_succeeds_when_previous_alias_does_not_exist():
    # Required subchecks: Previous alias does not exist, and user alias is set correctly.
    user_name = "testalias010"
    user_id = db_utils.create_user(username=user_name)
    user_alias = "testalias011"
    # Verify no alias is currently set
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    assert queried_user_alias == []
    # Make test user a premium user
    d.engine.execute("UPDATE profile SET config = config || 'd' WHERE userid = %(id)s AND config !~ 'd'", id=user_id)
    # Set alias and verify it is set correctly
    useralias.set(user_id, user_alias)
    queried_user_alias = useralias.select(userid=user_id)
    # The set alias should equal what the function returns.
    assert user_alias == queried_user_alias


def test_setting_alias_succeeds_when_previous_alias_exists():
    # Subchecks: 'previous' alias is set correctly, and new alias overwrites the old one
    user_name = "testalias012"
    user_id = db_utils.create_user(username=user_name)
    user_alias = "testalias013"
    user_previous_alias = "testalias014"
    # Make test user a premium user
    d.engine.execute("UPDATE profile SET config = config || 'd' WHERE userid = %(id)s AND config !~ 'd'", id=user_id)
    # Set 'previous' alias and verify it is set correctly
    useralias.set(user_id, user_previous_alias)
    queried_user_alias = useralias.select(userid=user_id)
    # Verify the 'previous' alias was set...
    assert user_previous_alias == queried_user_alias
    # Set and verify the new alias
    useralias.set(user_id, user_alias)
    queried_user_alias = useralias.select(userid=user_id)
    assert user_alias == queried_user_alias

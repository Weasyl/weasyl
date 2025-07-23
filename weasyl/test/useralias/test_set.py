import pytest

from weasyl.test import db_utils
from weasyl import useralias
from weasyl import define as d
from weasyl.error import WeasylError


@pytest.mark.usefixtures('db')
def test_setting_alias_fails_if_target_alias_exists():
    user_id = db_utils.create_user()
    user_id_existing = db_utils.create_user()
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id_existing, alias="existingalias")
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, "existingalias")
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_setting_alias_fails_if_target_username_exists():
    user_id = db_utils.create_user()
    db_utils.create_user(username="existinguser")
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, "existinguser")
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_setting_alias_fails_if_user_does_not_have_premium_status():
    user_id = db_utils.create_user()
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, "alias")
    assert 'InsufficientPermissions' == err.value.value


@pytest.mark.usefixtures('db')
def test_setting_alias_succeeds_when_previous_alias_does_not_exist():
    user_id = db_utils.create_user(premium=True)
    useralias.set(user_id, "alias")
    assert useralias.select(userid=user_id) == "alias"


@pytest.mark.usefixtures('db')
def test_setting_alias_succeeds_when_previous_alias_exists():
    user_id = db_utils.create_user(premium=True)
    useralias.set(user_id, "previousalias")
    useralias.set(user_id, "alias")
    assert useralias.select(userid=user_id) == "alias"

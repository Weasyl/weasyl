import unittest
import pytest

import db_utils
from weasyl import useralias
from weasyl import define as d
from weasyl.error import WeasylError


"""
Test section for: useralias.py::def select(userid, premium=True):
"""
def testSelect_SelectingAliasSucceedsIfPremiumParameterIsSetToTrue():
    # This is the default case
    user_id = db_utils.create_user()
    test_alias = "testalias0001"
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    query = useralias.select(userid=user_id, premium=True)
    # The manually set alias should equal what the function returns.
    assert test_alias == query

def testSelect_SelectingAliasSucceedsIfPremiumParameterIsSetToFalse():
    user_id = db_utils.create_user()
    test_alias = "testalias0002"
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    # The manually set alias should equal what the function returns.
    assert test_alias == queried_user_alias

def testSelect_SelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToTrue():
    user_id = db_utils.create_user()
    queried_user_alias = useralias.select(userid=user_id, premium=True)
    # Result when user has no alias set: should be a list, and be zero-length
    assert isinstance(queried_user_alias, list)
    assert not queried_user_alias

def testSelect_SelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToFalse():
    user_id = db_utils.create_user()
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    # Result when user has no alias set: should be a list, and be zero-length
    assert isinstance(queried_user_alias, list)
    assert not queried_user_alias

"""
Test section for: useralias.py::def set(userid, username):
"""
def testSet_SettingAliasFailsIfTargetAliasExists():
    user_id = db_utils.create_user(username="testalias003")
    user_id_existing = db_utils.create_user(username="testalias004")
    test_alias_existing = "testalias005"
    test_alias = test_alias_existing
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id_existing, alias=test_alias_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' in str(err)

def testSet_SettingAliasFailsIfTargetUsernameExists():
    user_name = "testalias006"
    user_name_existing = "testalias007"
    test_alias = user_name_existing
    user_id = db_utils.create_user(username=user_name)
    user_id_existing = db_utils.create_user(username=user_name_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' in str(err)

def testSet_SettingAliasFailsIfUserDoesNotHavePremiumStatus():
    user_name = "testalias008"
    user_id = db_utils.create_user(username=user_name)
    user_alias = "testalias009"
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, user_alias)
    assert 'InsufficientPermissions' in str(err)

def testSet_SettingAliasSucceedsWhenPreviousAliasDoesNotExist():
    # Required subchecks: Previous alias does not exist, and user alias is set correctly.
    user_name = "testalias010"
    user_id = db_utils.create_user(username=user_name)
    user_alias = "testalias011"
    # Verify no alias is currently set
    queried_user_alias = useralias.select(userid=user_id, premium=False)
    assert isinstance(queried_user_alias, list)
    assert len(queried_user_alias) == 0
    # Make test user a premium user
    d.engine.execute("UPDATE profile SET config = config || 'd' WHERE userid = %(id)s AND config !~ 'd'", id=user_id)
    # Set alias and verify it is set correctly
    useralias.set(user_id, user_alias)
    queried_user_alias = useralias.select(userid=user_id)
    # The set alias should equal what the function returns.
    assert user_alias == queried_user_alias

def testSet_SettingAliasSucceedsWhenPreviousAliasExists():
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

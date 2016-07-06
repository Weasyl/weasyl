import unittest
import pytest

import db_utils
from weasyl import useralias
from weasyl import define as d
from weasyl.error import WeasylError

TestAccountName_nameprefix = "testuseralias"
TestAccountName_counter = 0

"""
Section containing functions used within this suite of tests.
"""
class TestFunctions():
    def generateTestAccountName(self):
        global TestAccountName_counter
        global TestAccountName_nameprefix
        ret = TestAccountName_nameprefix + str(TestAccountName_counter)
        TestAccountName_counter += 1
        return ret
    def generateTokenString(self, size):
        import random
        import string
        return "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for i in range(size))

"""
Test section for: useralias.py::def select(userid, premium=True):
"""
def testSelect_SelectingAliasSucceedsIfPremiumParameterIsSetToTrue():
    # This is the default case
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    test_alias = TestFunctions().generateTestAccountName()
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    query = useralias.select(userid=user_id, premium=True)
    # The manually set alias should equal what the function returns.
    assert test_alias == query

def testSelect_SelectingAliasSucceedsIfPremiumParameterIsSetToFalse():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    test_alias = TestFunctions().generateTestAccountName()
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id, alias=test_alias)
    query = useralias.select(userid=user_id, premium=False)
    # The manually set alias should equal what the function returns.
    assert test_alias == query

def testSelect_SelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToTrue():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    query = useralias.select(userid=user_id, premium=True)
    # Result when user has no alias set: should be a list, and be zero-length
    assert isinstance(query, list)
    assert len(query) == 0

def testSelect_SelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToFalse():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    query = useralias.select(userid=user_id, premium=False)
    # Result when user has no alias set: should be a list, and be zero-length
    assert isinstance(query, list)
    assert len(query) == 0

"""
Test section for: useralias.py::def set(userid, username):
"""
def testSet_SettingAliasFailsIfTargetAliasExists():
    user_name = TestFunctions().generateTestAccountName()
    user_name_existing = TestFunctions().generateTestAccountName()
    test_alias_existing = TestFunctions().generateTestAccountName()
    test_alias = test_alias_existing
    user_id = db_utils.create_user(username=user_name)
    user_id_existing = db_utils.create_user(username=user_name_existing)
    d.engine.execute("INSERT INTO useralias VALUES (%(id)s, %(alias)s, 'p')", id=user_id_existing, alias=test_alias_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' in str(err)

def testSet_SettingAliasFailsIfTargetUsernameExists():
    user_name = TestFunctions().generateTestAccountName()
    user_name_existing = TestFunctions().generateTestAccountName()
    test_alias = user_name_existing
    user_id = db_utils.create_user(username=user_name)
    user_id_existing = db_utils.create_user(username=user_name_existing)
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, test_alias)
    assert 'usernameExists' in str(err)

def testSet_SettingAliasFailsIfUserDoesNotHavePremiumStatus():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    user_alias = TestFunctions().generateTestAccountName()
    with pytest.raises(WeasylError) as err:
        useralias.set(user_id, user_alias)
    assert 'InsufficientPermissions' in str(err)

def testSet_SettingAliasSucceedsWhenPreviousAliasDoesNotExist():
    # Required subchecks: Previous alias does not exist, and user alias is set correctly.
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    user_alias = TestFunctions().generateTestAccountName()
    # Verify no alias is currently set
    query = useralias.select(userid=user_id, premium=False)
    assert isinstance(query, list)
    assert len(query) == 0
    # Make test user a premium user
    d.engine.execute("UPDATE profile SET config = config || 'd' WHERE userid = %(id)s AND config !~ 'd'", id=user_id)
    # Set alias and verify it is set correctly
    useralias.set(user_id, user_alias)
    query = useralias.select(userid=user_id)
    # The set alias should equal what the function returns.
    assert user_alias == query

def testSet_SettingAliasSucceedsWhenPreviousAliasExists():
    # Subchecks: 'previous' alias is set correctly, and new alias overwrites the old one
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    user_alias = TestFunctions().generateTestAccountName()
    user_previous_alias = TestFunctions().generateTestAccountName()
    # Make test user a premium user
    d.engine.execute("UPDATE profile SET config = config || 'd' WHERE userid = %(id)s AND config !~ 'd'", id=user_id)
    # Set 'previous' alias and verify it is set correctly
    useralias.set(user_id, user_previous_alias)
    query = useralias.select(userid=user_id)
    # Verify the 'previous' alias was set...
    assert user_previous_alias == query
    # Set and verify the new alias
    useralias.set(user_id, user_alias)
    query = useralias.select(userid=user_id)
    assert user_alias == query

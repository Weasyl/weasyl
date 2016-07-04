import unittest

import db_utils
from weasyl import useralias
from weasyl import define as d
from weasyl.error import WeasylError
from array import array

TestAccountName_nameprefix = "testuseralias"
TestAccountName_counter = 0

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

class UseraliasSelectTestCase(unittest.TestCase):
    def testSelectingAliasSucceedsIfPremiumParameterIsSetToTrue(self):
        # This is the default case
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        test_alias = TestFunctions().generateTestAccountName()
        d.execute("INSERT INTO useralias VALUES (%i, '%s', 'p')", [user_id, test_alias])
        query = useralias.select(userid=user_id, premium=True)
        # The manually set alias should equal what the function returns.
        self.assertTrue(test_alias == query)

    def testSelectingAliasSucceedsIfPremiumParameterIsSetToFalse(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        test_alias = TestFunctions().generateTestAccountName()
        d.execute("INSERT INTO useralias VALUES (%i, '%s', '')", [user_id, test_alias])
        query = useralias.select(userid=user_id, premium=False)
        # The manually set alias should equal what the function returns.
        self.assertTrue(test_alias == query)
        
    def testSelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToTrue(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        query = useralias.select(userid=user_id, premium=True)
        # Result when user has no alias set: should be a list, and be zero-length
        self.assertTrue(isinstance(query, list))
        self.assertTrue(len(query) == 0)

    def testSelectingAliasWhenUserHasNoAliasReturnsZeroLengthArrayIfPremiumParameterIsSetToFalse(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        query = useralias.select(userid=user_id, premium=False)
        # Result when user has no alias set: should be a list, and be zero-length
        self.assertTrue(isinstance(query, list))
        self.assertTrue(len(query) == 0)

class UseraliasSetTestCase(unittest.TestCase):
    def testSettingAliasFailsIfTargetAliasExists(self):
        user_name = TestFunctions().generateTestAccountName()
        user_name_existing = TestFunctions().generateTestAccountName()
        test_alias_existing = TestFunctions().generateTestAccountName()
        test_alias = test_alias_existing
        user_id = db_utils.create_user(username=user_name)
        user_id_existing = db_utils.create_user(username=user_name_existing)
        d.execute("INSERT INTO useralias VALUES (%i, '%s', 'p')", [user_id_existing, test_alias_existing])
        self.assertRaisesRegexp(WeasylError, "usernameExists", useralias.set, user_id, test_alias)

    def testSettingAliasFailsIfTargetUsernameExists(self):
        user_name = TestFunctions().generateTestAccountName()
        user_name_existing = TestFunctions().generateTestAccountName()
        test_alias = user_name_existing
        user_id = db_utils.create_user(username=user_name)
        user_id_existing = db_utils.create_user(username=user_name_existing)
        self.assertRaisesRegexp(WeasylError, "usernameExists", useralias.set, user_id, test_alias)

    def testSettingAliasFailsIfUserDoesNotHavePremiumStatus(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        user_alias = TestFunctions().generateTestAccountName()
        self.assertRaisesRegexp(WeasylError, "InsufficientPermissions", useralias.set, user_id, user_alias)

    def testSettingAliasSucceedsWhenPreviousAliasDoesNotExist(self):
        # Required subchecks: Previous alias does not exist, and user alias is set correctly.
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        user_alias = TestFunctions().generateTestAccountName()
        # Verify no alias is currently set
        query = useralias.select(userid=user_id, premium=False)
        self.assertTrue(isinstance(query, list))
        self.assertTrue(len(query) == 0)
        # Make test user a premium user
        d.execute("UPDATE profile SET config = config || 'd' WHERE userid = %i AND config !~ 'd'", [user_id])
        # Set alias and verify it is set correctly
        useralias.set(user_id, user_alias)
        query = useralias.select(userid=user_id)
        # The set alias should equal what the function returns.
        self.assertTrue(user_alias == query)

    def testSettingAliasSucceedsWhenPreviousAliasExists(self):
        # Subchecks: 'previous' alias is set correctly, and new alias overwrites the old one
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        user_alias = TestFunctions().generateTestAccountName()
        user_previous_alias = TestFunctions().generateTestAccountName()
        # Make test user a premium user
        d.execute("UPDATE profile SET config = config || 'd' WHERE userid = %i AND config !~ 'd'", [user_id])
        # Set 'previous' alias and verify it is set correctly
        useralias.set(user_id, user_previous_alias)
        query = useralias.select(userid=user_id)
        # Verify the 'previous' alias was set...
        self.assertTrue(user_previous_alias == query)
        # Set and verify the new alias
        useralias.set(user_id, user_alias)
        query = useralias.select(userid=user_id)
        self.assertTrue(user_alias == query)

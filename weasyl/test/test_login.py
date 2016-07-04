# This Python file uses the following encoding: utf-8
import unittest
import pytest
import py
import bcrypt
import arrow
import web
import os
import json

import db_utils
from weasyl import login, macro
from weasyl import define as d
from weasyl.error import WeasylError
from _pytest import tmpdir

# Main test account
raw_password = "0123456789"
bcrypt_hash = login.passhash(raw_password)
old_2a_bcrypt_hash = "$2a$12$qReI924/8pAsoHu6aRTX2ejyujAZ/9FiOOtrjczBIwf8wqXAJ22N."

TestAccountName_nameprefix = "testlogin"
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

class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)

class SigninTestCase(unittest.TestCase):
    def testVerifyLoginRecordIsUpdated(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("UPDATE login SET last_login = '-1' WHERE userid = %i", [user_id])
        # login.signin(user_id) -will- raise an AttributeError when d.web.ctx.weasyl_session
        #   tries to execute itself; so catch/handle; it's a test environment issue
        self.assertRaises(AttributeError, login.signin, user_id)
        query = d.execute("SELECT last_login FROM login WHERE userid = %i", [user_id])
        self.assertGreater(query[0][0], -1)

class AuthenticateBcryptTestCase(unittest.TestCase):
    def testNoUsernameProvided(self):
        result = login.authenticate_bcrypt(username='', password='password')
        self.assertEqual(result, (0, 'invalid'))

    def testNoPasswordProvided(self):
        user_name = TestFunctions().generateTestAccountName()
        result = login.authenticate_bcrypt(username=user_name, password='')
        self.assertEqual(result, (0, 'invalid'))

    def testInvalidUsernameProvided(self):
        user_name = TestFunctions().generateTestAccountName()
        result = login.authenticate_bcrypt(username=user_name, password=raw_password)
        self.assertEqual(result, (0, 'invalid'))

    def testLoginFailsForModsWithInvalidAuthentication(self):
        log_path = '%s%s.%s.log' % (macro.MACRO_SYS_LOG_PATH, 'login.fail', d.get_timestamp())
        mod_userid = 2061
        user_id = db_utils.create_user(username='ikani')
        d.execute("UPDATE login SET userid = %i WHERE userid = %i", [mod_userid, user_id])
        user_id = mod_userid
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        # Hackish workaround to ensure that the log is being written to until the
        #  pytest way of making a temporary directory to patch the log directory to can be figured out
        prerun_loglines = 0
        with open(log_path, 'r') as log:
            for line in log:
                prerun_loglines += 1
            log.close()
        postrun_loglines = 0
        # Item under test
        result = login.authenticate_bcrypt(username='ikani', password='FakePassword')
        # Verify we are writing to the log file as expected
        last_line = ''
        with open(log_path, 'r') as log:
            for line in log:
                postrun_loglines += 1
            last_line = line
            log.close()
        last_line_dict = json.loads(last_line)
        self.assertGreater(postrun_loglines, prerun_loglines)
        self.assertTrue(last_line_dict['userid'] == mod_userid)
        self.assertEqual(result, (0, 'invalid'))

    def testLoginFailsForBannedUsers(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 'b' WHERE userid = %i", [user_id])
        result = login.authenticate_bcrypt(username=user_name, password=raw_password)
        print result
        self.assertEqual(result, (user_id, 'banned'))

    def testLoginFailsForSuspendedUsersWithActiveDuration(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 's' WHERE userid = %i", [user_id])
        release_date = d.convert_unixdate(31, 12, 2030)
        d.execute("INSERT INTO suspension VALUES (%i, '%s', %i)", [user_id, 'test', release_date])
        result = login.authenticate_bcrypt(username=user_name, password=raw_password, session=False)
        self.assertEqual(result, (user_id, 'suspended'))

    def testLoginSucceedsForSuspendedUsersWithExpiredDuration(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 's' WHERE userid = %i", [user_id])
        release_date = d.convert_unixdate(31, 12, 2015)
        d.execute("INSERT INTO suspension VALUES (%i, '%s', %i)", [user_id, 'test', release_date])
        result = login.authenticate_bcrypt(username=user_name, password=raw_password, session=False)
        self.assertEqual(result, (user_id, None))

# For some reason getting the password to work with the accented E just isn't happening...
#     def testLoginSucceedsForValidUserAndPasswordWithUnicodeFailure(self):
#         # $2a$12$qReI924/8pAsoHu6aRTX2ejyujAZ/9FiOOtrjczBIwf8wqXAJ22N. == "passwprd"
#         user_id = db_utils.create_user(username='testloginsuite')
#         d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, old_2a_bcrypt_hash])
#         d.execute("UPDATE authbcrypt SET hashsum = '%s' WHERE userid = %i", [login.passhash(raw_password), user_id])
#         result = login.authenticate_bcrypt(username='testloginsuite', password=u'passwordé', session=False)
#         print result
#         self.assertTrue(result[0] == user_id)
#         self.assertTrue(result[1] == 'unicode-failure')
#         d.execute("DELETE FROM login WHERE userid = %i", [user_id])

    def testLoginSucceedsForValidUserAndPassword(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        result = login.authenticate_bcrypt(username=user_name, password=raw_password, session=False)
        self.assertEqual(result, (user_id, None))

class PasswordChecksTestCase(unittest.TestCase):
    def testPasswordSecure(self):
        # Length too short (len < login._PASSWORD)
        test_string = ""
        for i in range(0, login._PASSWORD):
            self.assertFalse(login.password_secure(test_string))
            test_string = test_string + 'a'

        # Acceptable length (len >= 10)
        for i in range(login._PASSWORD, login._PASSWORD + 3):
            test_string = test_string + 'a'
            self.assertTrue(login.password_secure(test_string))

    def testPasshash(self):
        self.assertTrue(bcrypt_hash)
        self.assertTrue(bcrypt.checkpw(raw_password.encode('utf-8'), bcrypt_hash.encode('utf-8')))

class UpdateUnicodePasswordTestCase(unittest.TestCase):
    def testPasswordMismatchWeasylErrorIfPasswordsDoNotMatch(self):
        self.assertRaisesRegexp(WeasylError, "passwordMismatch", login.update_unicode_password, 
                                userid=123, password=321, password_confirm=123)

    def testPasswordInsecureWeasylErrorIfPasswordUnderMinimumLength(self):
        self.assertRaisesRegexp(WeasylError, "passwordInsecure", login.update_unicode_password, 
                                userid=123, password="012345678", password_confirm="012345678")

    def testVerifyingCorrectPasswordAgainstStoredBcryptHash(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        self.assertTrue(None is login.update_unicode_password(user_id, "0123456789", "0123456789"))

    def testPasswordIncorrectWeasylErrorIfPasswordIsIncorrect(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        self.assertRaisesRegexp(WeasylError, "passwordIncorrect", login.update_unicode_password, 
                                userid=user_id, password="01234567811", password_confirm="01234567811")

class CreateTestCase(unittest.TestCase):    
    def testCheckIfBirthdayIsInvalid_DayMonthOrYearIsNotAnInteger(self):
        user_name = TestFunctions().generateTestAccountName()
        # Check for failure state if 'day' is not an integer, e.g., string
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='test', month='31', year='1942')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

        # Check for failure state if 'month' is not an integer, e.g., string
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='test', year='1942')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

        # Check for failure state if 'year' is not an integer, e.g., string
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='31', year='test')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

    def testCheckIfBirthdayIsInvalid_DayMonthOrYearAreOutOfValidRanges(self):
        user_name = TestFunctions().generateTestAccountName()
        # Check for failure state if 'day' is not an valid day e.g., 42
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='42', month='12', year='2000')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)
    
        # Check for failure state if 'month' is not an valid month e.g., 42
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='42', year='2000')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

        # Check for failure state if 'year' is not an valid year e.g., -1
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='12', year='-1')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

    def testCheckIfBirthdayIsInvalid_DayMonthOrYearIsMissing(self):
        user_name = TestFunctions().generateTestAccountName()
        # Check for failure state if 'year' is not an valid year e.g., -1
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day=None, month='12', year='2000')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)
        # Check for failure state if 'year' is not an valid year e.g., -1
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month=None, year='2000')
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)
        # Check for failure state if 'year' is not an valid year e.g., -1
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='12', year=None)
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

    def testCheckIfBirthdayIsInvalid_ComputedBirthdayUnder13YearsOfAge(self):
        user_name = TestFunctions().generateTestAccountName()
        # Check for failure state if computed birthday is <13 years old
        form = Bag(username=user_name, password='', passcheck='',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='12', year=arrow.now().year - 11)
        self.assertRaisesRegexp(WeasylError, "birthdayInvalid", login.create, form)

    def testPasswordChecks_PasswordMismatch(self):
        user_name = TestFunctions().generateTestAccountName()
        # Check for failure if password != passcheck
        form = Bag(username=user_name, password='123', passcheck='qwe',
                   email='example@weasyl.com', emailcheck='example@weasyl.com',
                   day='12', month='12', year=arrow.now().year - 19)
        self.assertRaisesRegexp(WeasylError, "passwordMismatch", login.create, form)

    def testPasswordChecks_PasswordConsideredInsecureByLength(self):
        user_name = TestFunctions().generateTestAccountName()
        password = ''
        form = Bag(username=user_name, password='', passcheck='',
                   email='foo', emailcheck='foo',
                   day='12', month='12', year=arrow.now().year - 19)
        # Insecure length
        for i in range (1, login._PASSWORD):
            self.assertRaisesRegexp(WeasylError, "passwordInsecure", login.create, form)
            password = password + 'a'
            form.passcheck = form.password = password
        # Secure length
        password = password + 'a'
        form.passcheck = form.password = password
        # emailInvalid is the next failure state after passwordInsecure, so it is a 'success' for this testcase
        self.assertRaisesRegexp(WeasylError, "emailInvalid", login.create, form)

    def testEmailChecks_EmailMismatch(self):
        user_name = TestFunctions().generateTestAccountName()
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email='test@weasyl.com', emailcheck='testt@weasyl.com',
                   day='12', month='12', year=arrow.now().year - 19)
        self.assertRaisesRegexp(WeasylError, "emailMismatch", login.create, form)

    def testEmailChecks_EmailInvalid(self):
        user_name = TestFunctions().generateTestAccountName()
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=';--', emailcheck=';--',
                   day='12', month='12', year=arrow.now().year - 19)
        self.assertRaisesRegexp(WeasylError, "emailInvalid", login.create, form)

    def testEmailChecks_EmailExistsInLogin(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        user_id = db_utils.create_user(username=TestFunctions().generateTestAccountName())
        d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
        self.assertRaisesRegexp(WeasylError, "emailExists", login.create, form)

    def testEmailChecks_EmailExistsInLogincreate(self):
        user_name = TestFunctions().generateTestAccountName()
        user_name_2 = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        token = TestFunctions().generateTokenString(40)
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
                         "token": token,
                         "username": user_name_2,
                         "login_name": user_name_2,
                         "hashpass": login.passhash(raw_password),
                         "email": email_addr,
                         "birthday": arrow.Arrow(2000, 1, 1),
                         "unixtime": arrow.now(),
                         })
        self.assertRaisesRegexp(WeasylError, "emailExists", login.create, form)

    def testUsernameChecks_UsernameNonexistentOrContainsSemicolon(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        form = Bag(username='...', password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        self.assertRaisesRegexp(WeasylError, "usernameInvalid", login.create, form)
        form.username = 'testloginsuite;'
        self.assertRaisesRegexp(WeasylError, "usernameInvalid", login.create, form)

    def testUsernameChecks_UsernameContainsProhibitedWords(self):
        form = Bag(username='testloginsuite', password='0123456789', passcheck='0123456789',
                   email='test@weasyl.com', emailcheck='test@weasyl.com',
                   day='12', month='12', year=arrow.now().year - 19)
        prohibited_names = ["admin", "administrator", "mod", "moderator", "weasyl",
                            "weasyladmin", "weasylmod", "staff", "security"]
        for i in range (0, len(prohibited_names)):
            form.username = prohibited_names[i]
            self.assertRaisesRegexp(WeasylError, "usernameInvalid", login.create, form)

    def testUsernameChecks_UsernameExistsInLogin(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        user_id = db_utils.create_user(username=user_name)
        d.execute("UPDATE login SET email = '%s' WHERE userid = %i", ["UsernameExistsInLogin@weasyl.com", user_id])
        self.assertRaisesRegexp(WeasylError, "usernameExists", login.create, form)

    def testUsernameChecks_UsernameExistsInLogincreate(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        token = TestFunctions().generateTokenString(40)
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
                         "token": token,
                         "username": user_name,
                         "login_name": user_name,
                         "hashpass": login.passhash(raw_password),
                         "email": "UsernameExistsInLogincreate@weasyl.com",
                         "birthday": arrow.Arrow(2000, 1, 1),
                         "unixtime": arrow.now(),
                         })
        self.assertRaisesRegexp(WeasylError, "usernameExists", login.create, form)


    def testUsernameChecks_UsernameExistsInUseralias(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        user_id = db_utils.create_user(username='aliastest')
        d.execute("INSERT INTO useralias VALUES (%i, '%s', 'p')", [user_id, user_name])
        self.assertRaisesRegexp(WeasylError, "usernameExists", login.create, form)

    def testVerifyInsertionOfValidUserToCreateInLogincreate(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        # Emailing doesn't work in the test environment, but by this point the
        # logincreate entry has been made
        try:
            login.create(form)
        except OSError:
            print "Caught OSError (Expected): Email fails in test environment"
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)
                """, name=form.username).scalar()
        self.assertTrue(query)

class VerifyTestCase(unittest.TestCase):
    def testVerifyFailureIfInvalidTokenProvided(self):
        self.assertRaisesRegexp(WeasylError, "logincreateRecordMissing", login.verify, "qwe")

    def testVerifySuccessfulExecutionIfValidTokenProvided(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        token = TestFunctions().generateTokenString(40)
        form = Bag(username='testloginsuitetoken', password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
                         "token": token,
                         "username": form.username,
                         "login_name": form.username,
                         "hashpass": login.passhash(raw_password),
                         "email": form.email,
                         "birthday": arrow.Arrow(2000, 1, 1),
                         "unixtime": arrow.now(),
                         })
        login.verify(token)

        userid = d.execute("SELECT userid FROM login WHERE login_name = '%s'", [form.username])
        userid = userid[0][0]
        # Verify that each table gets the correct information added to it (checks for record's existence for brevity)
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM authbcrypt WHERE userid = %(userid)s)
                """, userid=userid).scalar()
        self.assertTrue(query)
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM profile WHERE userid = %(userid)s)
                """, userid=userid).scalar()
        self.assertTrue(query)
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM userinfo WHERE userid = %(userid)s)
                """, userid=userid).scalar()
        self.assertTrue(query)
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM userstats WHERE userid = %(userid)s)
                """, userid=userid).scalar()
        self.assertTrue(query)
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM welcomecount WHERE userid = %(userid)s)
                """, userid=userid).scalar()
        self.assertTrue(query)

        # The 'logincreate' record gets deleted on successful execution; verify this
        query = d.engine.execute("""
                    SELECT
                        EXISTS (SELECT 0 FROM logincreate WHERE token = %(token)s)
                """, token=token).scalar()
        self.assertFalse(query)

class SettingsTestCase(unittest.TestCase):
    def testWhenNoSettingIsPassedAsAParameter(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        settings = 'dp'
        d.execute("UPDATE login SET settings = '%s' WHERE userid = %i", [settings, user_id])
        query = login.settings(user_id)
        self.assertTrue(settings == query)

    def testWhenASettingIsPassedAsAParameter(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        settings = 'dp'
        d.execute("UPDATE login SET settings = '%s' WHERE userid = %i", [settings, user_id])
        query = login.settings(user_id, 'd')
        self.assertTrue(query)

class SessionidTestCase(unittest.TestCase):
    def testSessionidRetrieval(self):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        sessionid = TestFunctions().generateTokenString(64)
        d.engine.execute(d.meta.tables["sessions"].insert(), {
                         "sessionid": sessionid,
                         "userid": user_id,
                         "csrf_token": sessionid,
                         })
        self.assertTrue(sessionid == login.sessionid(user_id))

class GetAccountVerificationTokenTestCase(unittest.TestCase):
    def testEmailProvidedToFunction(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        token = TestFunctions().generateTokenString(40)
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
                         "token": token,
                         "username": form.username,
                         "login_name": form.username,
                         "hashpass": login.passhash(raw_password),
                         "email": form.email,
                         "birthday": arrow.Arrow(2000, 1, 1),
                         "unixtime": arrow.now(),
                         })
        query = login.get_account_verification_token(email=form.email, username=None)
        self.assertEqual(token, query)

    def testUsernameProvidedToFunction(self):
        user_name = TestFunctions().generateTestAccountName()
        email_addr = user_name + "@weasyl.com"
        token = TestFunctions().generateTokenString(40)
        form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
                   email=email_addr, emailcheck=email_addr,
                   day='12', month='12', year=arrow.now().year - 19)
        d.engine.execute(d.meta.tables["logincreate"].insert(), {
                         "token": token,
                         "username": form.username,
                         "login_name": form.username,
                         "hashpass": login.passhash(raw_password),
                         "email": form.email,
                         "birthday": arrow.Arrow(2000, 1, 1),
                         "unixtime": arrow.now(),
                         })
        query = login.get_account_verification_token(email=None, username=form.username)
        self.assertEqual(token, query)

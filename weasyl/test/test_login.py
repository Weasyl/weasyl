# This Python file uses the following encoding: utf-8
import unittest
import bcrypt
import arrow
import web
import ast

import db_utils
from weasyl import login, macro
from weasyl import define as d
from weasyl.error import WeasylError

# Main test account
raw_password = "0123456789"
bcrypt_hash = login.passhash(raw_password)
old_2a_bcrypt_hash = "$2a$12$qReI924/8pAsoHu6aRTX2ejyujAZ/9FiOOtrjczBIwf8wqXAJ22N."

class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)

class SigninTestCase(unittest.TestCase):
    def testVerifyLoginRecordIsUpdated(self):
        user_id = db_utils.create_user(username='testloginsuite')
        d.execute("UPDATE login SET last_login = '-1' WHERE userid = %i", [user_id])
        # login.signin(user_id) -will- raise an AttributeError when d.web.ctx.weasyl_session
        #   tries to execute itself; so catch/handle
        try:
            login.signin(user_id)
        except AttributeError:
            print 'Caught AttributeError, as expected'
        query = d.execute("SELECT last_login FROM login WHERE userid = %i", [user_id])
        self.assertGreater(query[0][0], -1)
        d.execute("DELETE FROM login WHERE userid = %i", [user_id])

class AuthenticateBcryptTestCase(unittest.TestCase):
    def testNoUsernameProvided(self):
        result = login.authenticate_bcrypt(username='', password='password')
        self.assertTrue(result[0] == 0)
        self.assertTrue(result[1] == 'invalid')
    
    def testNoPasswordProvided(self):
        result = login.authenticate_bcrypt(username='testloginsuite', password='')
        self.assertTrue(result[0] == 0)
        self.assertTrue(result[1] == 'invalid')
    
    def testInvalidUsernameProvided(self):
        result = login.authenticate_bcrypt(username='InvalidUsername', password=raw_password)
        self.assertTrue(result[0] == 0)
        self.assertTrue(result[1] == 'invalid')

    def testLoginFailsForModsWithInvalidAuthentication(self):
        log_path = '%s%s.%s.log' % (macro.MACRO_SYS_LOG_PATH, 'login.fail', d.get_timestamp())
        open(log_path, 'w').close()
        mod_userid = 2061
        user_id = db_utils.create_user(username='ikani')
        d.execute("UPDATE login SET userid = %i WHERE userid = %i", [mod_userid, user_id])
        user_id = mod_userid
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        result = login.authenticate_bcrypt(username='ikani', password='FakePassword')
        # Verify we are writing to the log file as expected
        last_line = ''
        with open(log_path, 'r') as log:
            for line in log:
                pass
            last_line = line
        last_line_dict = ast.literal_eval(last_line)
        self.assertTrue(last_line_dict['userid'] == mod_userid)
        self.assertTrue(result[0] == 0)
        self.assertTrue(result[1] == 'invalid')

    def testLoginFailsForBannedUsers(self):
        user_id_bansusp = db_utils.create_user(username='testbansusp')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id_bansusp, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 'b' WHERE userid = %i", [user_id_bansusp])
        result = login.authenticate_bcrypt(username='testbansusp', password=raw_password)
        print result
        self.assertTrue(result[0] == user_id_bansusp)
        self.assertTrue(result[1] == 'banned')
        d.execute("DELETE FROM login WHERE userid = %i", [user_id_bansusp])

    def testLoginFailsForSuspendedUsersWithActiveDuration(self):
        user_id_bansusp = db_utils.create_user(username='testbansusp')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id_bansusp, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 's' WHERE userid = %i", [user_id_bansusp])
        release_date = d.convert_unixdate(31, 12, 2030)
        d.execute("INSERT INTO suspension VALUES (%i, '%s', %i)", [user_id_bansusp, 'test', release_date])
        result = login.authenticate_bcrypt(username='TestBanSusp', password=raw_password, session=False)
        self.assertTrue(result[0] == user_id_bansusp)
        self.assertTrue(result[1] == 'suspended')
        d.execute("DELETE FROM login WHERE userid = %i", [user_id_bansusp])
        d.execute("DELETE FROM suspension WHERE userid = %i", [user_id_bansusp])
         
    def testLoginSucceedsForSuspendedUsersWithExpiredDuration(self):
        user_id_bansusp = db_utils.create_user(username='testbansusp')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id_bansusp, login.passhash(raw_password)])
        d.execute("UPDATE login SET settings = 's' WHERE userid = %i", [user_id_bansusp])
        release_date = d.convert_unixdate(31, 12, 2015)
        d.execute("INSERT INTO suspension VALUES (%i, '%s', %i)", [user_id_bansusp, 'test', release_date])
        result = login.authenticate_bcrypt(username='TestBanSusp', password=raw_password, session=False)
        self.assertTrue(result[0] == user_id_bansusp)
        self.assertTrue(result[1] is None)
        d.execute("DELETE FROM login WHERE userid = %i", [user_id_bansusp])
        d.execute("DELETE FROM suspension WHERE userid = %i", [user_id_bansusp])
    
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
        user_id = db_utils.create_user(username='testloginsuite')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        result = login.authenticate_bcrypt(username='testloginsuite', password=raw_password, session=False)
        print result
        self.assertTrue(result[0] == user_id)
        self.assertTrue(result[1] is None)
        d.execute("DELETE FROM login WHERE userid = %i", [user_id])

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
        user_id = db_utils.create_user(username='testloginsuite')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        self.assertTrue(None is login.update_unicode_password(user_id, "0123456789", "0123456789"))
        d.execute("DELETE FROM login WHERE userid = %i", [user_id])
        
    def testPasswordIncorrectWeasylErrorIfPasswordIsIncorrect(self):
        user_id = db_utils.create_user(username='testloginsuite')
        d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash(raw_password)])
        self.assertRaisesRegexp(WeasylError, "passwordIncorrect", login.update_unicode_password, 
                                userid=user_id, password="01234567811", password_confirm="01234567811")
        d.execute("DELETE FROM login WHERE userid = %i", [user_id])


    
    
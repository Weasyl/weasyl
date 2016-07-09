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


"""
Section containing functions used within this suite of tests.
"""
# Main test account
raw_password = "0123456789"
class TestFunctions():
    def generateTokenString(self, size):
        import random
        import string
        return "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for i in range(size))

class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)

"""
Test section for: login.py::def signin(userid):
"""
def testSignin_VerifyLoginRecordIsUpdated():
    user = db_utils.create_user(return_user_definition=True)
    d.engine.execute("UPDATE login SET last_login = -1 WHERE userid = %(id)s", id=user['id'])
    # login.signin(user_id) -will- raise an AttributeError when d.web.ctx.weasyl_session
    #   tries to execute itself; so catch/handle; it's a test environment issue
    with pytest.raises(AttributeError) as err:
        login.signin(user['id'])
    print str(err)
    last_login = d.engine.scalar("SELECT last_login FROM login WHERE userid = %(id)s", id=user['id'])
    assert last_login > -1

"""
Test section for: login.py::def authenticate_bcrypt(username, password, session=True):
"""
def testAuthenticateBcrypt_NoUsernameProvided():
    result = login.authenticate_bcrypt(username='', password='password')
    assert result == (0, 'invalid')

def testAuthenticateBcrypt_NoPasswordProvided():
    user_name = "NoPasswordProvided"
    result = login.authenticate_bcrypt(username=user_name, password='')
    assert result == (0, 'invalid')

def testAuthenticateBcrypt_InvalidUsernameProvided():
    user_name = "InvalidUsernameProvided"
    result = login.authenticate_bcrypt(username=user_name, password=raw_password)
    assert result == (0, 'invalid')

def testAuthenticateBcrypt_VerifyLoginFailsForAllUsersIfIncorrectPasswordProvided():
    random_password = "ThisIsARandomPassword"
    user = db_utils.create_user(password=random_password, return_user_definition=True)
    another_random_password = "ThisIsNotTheSamePassword"
    result = login.authenticate_bcrypt(username=user['name'], password=another_random_password)
    assert result == (0, 'invalid')

def testAuthenticateBcrypt_LoginFailsForModsWithInvalidAuthentication(tmpdir, monkeypatch):
    # Set the temporary directory for the log file
    monkeypatch.setenv(macro.MACRO_SYS_LOG_PATH, tmpdir + "/")
    log_path = '%s%s.%s.log' % (macro.MACRO_SYS_LOG_PATH, 'login.fail', d.get_timestamp())
    mod_userid = 2061
    user_id = db_utils.create_user(username='ikani', password=raw_password, user_id=mod_userid)
    # Ensure we are actually writing to the file by counting the file's lines
    prerun_loglines = 0
    # The file might not exist; this is fine; ignore
    try:
        with open(log_path, 'r') as log:
            for line in log:
                prerun_loglines += 1
            log.close()
    except IOError:
        pass
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
    assert postrun_loglines > prerun_loglines
    assert last_line_dict['userid'] == mod_userid
    assert result == (0, 'invalid')

def testAuthenticateBcrypt_LoginFailsForBannedUsers():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    d.engine.execute("UPDATE login SET settings = 'b' WHERE userid = %(id)s", id=user['id'])
    result = login.authenticate_bcrypt(username=user['name'], password=raw_password)
    assert result == (user['id'], 'banned')

def testAuthenticateBcrypt_LoginFailsForSuspendedUsersWithActiveDuration():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    d.engine.execute("UPDATE login SET settings = 's' WHERE userid = %(id)s", id=user['id'])
    release_date = d.convert_unixdate(31, 12, 2030)
    d.engine.execute("INSERT INTO suspension VALUES (%(id)s, %(reason)s, %(rel)s)",
                     id=user['id'], reason='test', rel=release_date)
    result = login.authenticate_bcrypt(username=user['name'], password=raw_password, session=False)
    assert result == (user['id'], 'suspended')

def testAuthenticateBcrypt_LoginSucceedsForSuspendedUsersWithExpiredDuration():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    d.engine.execute("UPDATE login SET settings = 's' WHERE userid = %(id)s", id=user['id'])
    release_date = d.convert_unixdate(31, 12, 2015)
    d.engine.execute("INSERT INTO suspension VALUES (%(id)s, %(reason)s, %(rel)s)",
                     id=user['id'], reason='test', rel=release_date)
    result = login.authenticate_bcrypt(username=user['name'], password=raw_password, session=False)
    assert result == (user['id'], None)

def testAuthenticateBcrypt_LoginSucceedsForValidUserAndPasswordWithUnicodeFailure():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    # This hash decodes to "password"
    old_2a_bcrypt_hash = "$2a$12$qReI924/8pAsoHu6aRTX2ejyujAZ/9FiOOtrjczBIwf8wqXAJ22N."
    d.engine.execute("UPDATE authbcrypt SET hashsum = %(hash)s WHERE userid = %(id)s",
                     hash=old_2a_bcrypt_hash, id=user['id'])
    result = login.authenticate_bcrypt(user['name'], u"passwordé", session=False)
    assert result == (user['id'], 'unicode-failure')

def testAuthenticateBcrypt_LoginSucceedsForValidUserAndPassword():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    result = login.authenticate_bcrypt(username=user['name'], password=raw_password, session=False)
    assert result == (user['id'], None)

"""
Test section for functions:
a) login.py::def password_secure(password):
b) login.py::def passhash(password):
"""
def test_password_secure__verify_it_functions_as_expected():
    # Length too short (len < login._PASSWORD)
    test_string = ""
    for i in range(0, login._PASSWORD):
        assert not login.password_secure(test_string)
        test_string = test_string + 'a'

    # Acceptable length (len >= 10)
    for i in range(login._PASSWORD, login._PASSWORD + 3):
        test_string = test_string + 'a'
        assert login.password_secure(test_string)

def test_passhash__verify_it_functions_as_expected():
    # Generate a bcrypt hash from .passhash
    bcrypt_hash = login.passhash(raw_password)
    assert bcrypt_hash
    # Verify the password hashes correctly.
    assert bcrypt.checkpw(raw_password.encode('utf-8'), bcrypt_hash.encode('utf-8'))

"""
Test section for: login.py::def update_unicode_password(userid, password, password_confirm):
"""
def testUpdateUnicodePassword_PasswordMismatchWeasylErrorIfPasswordsDoNotMatch():
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(123, '321', '123')
    assert 'passwordMismatch' in str(err)

def testUpdateUnicodePassword_PasswordInsecureWeasylErrorIfPasswordUnderMinimumLength():
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(123, '012345678', '012345678')
    assert 'passwordInsecure' in str(err)

def testUpdateUnicodePassword_VerifyingCorrectPasswordAgainstStoredBcryptHash():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    assert login.update_unicode_password(user['id'], "0123456789", "0123456789") is None

def testUpdateUnicodePassword_PasswordIncorrectWeasylErrorIfPasswordIsIncorrect():
    user = db_utils.create_user(password=raw_password, return_user_definition=True)
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(userid=user['id'], password='01234567811', password_confirm='01234567811')
    assert 'passwordIncorrect' in str(err)

"""
Test section for: login.py::def create(form):
"""
def testCreate_CheckIfBirthdayIsInvalid_DayMonthOrYearIsNotAnInteger():
    user_name = "BDayInvalid0001"
    # Check for failure state if 'day' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='test', month='31', year='1942')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'month' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='test', year='1942')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'year' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='31', year='test')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

def testCreate_CheckIfBirthdayIsInvalid_DayMonthOrYearAreOutOfValidRanges():
    user_name = "BDayInvalid0002"
    # Check for failure state if 'day' is not an valid day e.g., 42
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='42', month='12', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'month' is not an valid month e.g., 42
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='42', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='12', year='-1')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

def testCreate_CheckIfBirthdayIsInvalid_DayMonthOrYearIsMissing():
    user_name = "BDayInvalid0003"
    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day=None, month='12', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month=None, year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='12', year=None)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

def testCreate_CheckIfBirthdayIsInvalid_ComputedBirthdayUnder13YearsOfAge():
    user_name = "TooYoung0001"
    # Check for failure state if computed birthday is <13 years old
    form = Bag(username=user_name, password='', passcheck='',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='12', year=arrow.now().year - 11)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' in str(err)

def testCreate_PasswordChecks_PasswordMismatch():
    user_name = "PWMismatch0001"
    # Check for failure if password != passcheck
    form = Bag(username=user_name, password='123', passcheck='qwe',
               email='example@weasyl.com', emailcheck='example@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'passwordMismatch' in str(err)

def testCreate_PasswordChecks_PasswordConsideredInsecureByLength():
    user_name = "PWInsecure0001"
    password = ''
    form = Bag(username=user_name, password='', passcheck='',
               email='foo', emailcheck='foo',
               day='12', month='12', year=arrow.now().year - 19)
    # Insecure length
    for i in range (1, login._PASSWORD):
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'passwordInsecure' in str(err)
        password = password + 'a'
        form.passcheck = form.password = password
    # Secure length
    password = password + 'a'
    form.passcheck = form.password = password
    # emailInvalid is the next failure state after passwordInsecure, so it is a 'success' for this testcase
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' in str(err)

def testCreate_EmailChecks_EmailMismatch():
    user_name = "EmailMismatch0001"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email='test@weasyl.com', emailcheck='testt@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailMismatch' in str(err)
def testCreate_EmailChecks_EmailInvalid():
    user_name = "EmailInvalid0001"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=';--', emailcheck=';--',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' in str(err)

def testCreate_EmailChecks_EmailExistsInLogin():
    user_name = "emailexistsinlogin"
    email_addr = user_name + "@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    user_id = db_utils.create_user(username=user_name, email_addr=email_addr)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailExists' in str(err)

def testCreate_EmailChecks_EmailExistsInLogincreate():
    user_name = "EmailExLoginCreate001"
    user_name_2 = "EmailExLoginCreate002"
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
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailExists' in str(err)

def testCreate_UsernameChecks_UsernameNonexistentOrContainsSemicolon():
    email_addr = "UsernameNonexistentOrContainsSemicolon" + "@weasyl.com"
    form = Bag(username='...', password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameInvalid' in str(err)
    form.username = 'testloginsuite;'
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameInvalid' in str(err)

def testCreate_UsernameChecks_UsernameContainsProhibitedWords():
    form = Bag(username='testloginsuite', password='0123456789', passcheck='0123456789',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    prohibited_names = ["admin", "administrator", "mod", "moderator", "weasyl",
                        "weasyladmin", "weasylmod", "staff", "security"]
    for i, name in enumerate(prohibited_names):
        form.username = name
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'usernameInvalid' in str(err)

def testCreate_UsernameChecks_UsernameExistsInLogin():
    user_name = "usernameexists0001"
    email_addr = user_name + "@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    user_id = db_utils.create_user(username=user_name, email_addr="UsernameExistsInLogin@weasyl.com")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' in str(err)

def testCreate_UsernameChecks_UsernameExistsInLogincreate():
    user_name = "usernameexists0002"
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
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' in str(err)

def testCreate_UsernameChecks_UsernameExistsInUseralias():
    user_name = "usernameexists0003"
    email_addr = user_name + "@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    user_id = db_utils.create_user(username='aliastest')
    d.engine.execute("INSERT INTO useralias VALUES (%(userid)s, %(username)s, 'p')", userid=user_id, username=user_name)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' in str(err)

def testCreate_VerifyInsertionOfValidUserToCreateInLogincreate():
    user_name = "validuser0001"
    email_addr = user_name + "@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    # Emailing doesn't work in the test environment, but by this point the
    # logincreate entry has been made
    with pytest.raises(OSError) as err:
        login.create(form)
    # This record should exist when this function completes successfully
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)
                """, name=form.username)

"""
Test section for: login.py::def verify(token):
"""
def testVerify_VerifyFailureIfInvalidTokenProvided():
    with pytest.raises(WeasylError) as err:
        login.verify("qwe")
    assert 'logincreateRecordMissing' in str(err)

def testVerify_VerifySuccessfulExecutionIfValidTokenProvided():
    user_name = "validuser0004"
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

    userid = d.engine.scalar("SELECT userid FROM login WHERE login_name = %(name)s", name=form.username)
    # Verify that each table gets the correct information added to it (checks for record's existence for brevity)
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM authbcrypt WHERE userid = %(userid)s)
                """, userid=userid)
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM profile WHERE userid = %(userid)s)
                """, userid=userid)
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM userinfo WHERE userid = %(userid)s)
                """, userid=userid)
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM userstats WHERE userid = %(userid)s)
                """, userid=userid)
    assert d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM welcomecount WHERE userid = %(userid)s)
                """, userid=userid)

    # The 'logincreate' record gets deleted on successful execution; verify this
    assert not d.engine.scalar("""
                SELECT
                    EXISTS (SELECT 0 FROM logincreate WHERE token = %(token)s)
                """, token=token)

"""
Test section for: login.py::def get_account_verification_token(email=None, username=None):
"""
def testGetAccountVerificationToken_EmailProvidedToFunction():
    user_name = "validuser0002"
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
    acct_verification_token = login.get_account_verification_token(email=form.email, username=None)
    assert token == acct_verification_token

def testGetAccountVerificationToken_UsernameProvidedToFunction():
    user_name = "validuser0003"
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
    acct_verification_token = login.get_account_verification_token(email=None, username=form.username)
    assert token == acct_verification_token

import unittest
import pytest
import py
import bcrypt
import arrow
import web
import os
import json

import db_utils
from weasyl import resetpassword, macro, login
from weasyl import define as d
from weasyl.error import WeasylError



"""
Section containing functions used within this suite of tests.
"""
TestAccountName_nameprefix = "testresetpassword"
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

"""
Test section for: resetpassword.py::def checktoken(token):
"""
def testChecktoken_VerifyFalseReturnedIfTokenDoesNotExistInForgotpassword():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    token = TestFunctions().generateTokenString(100)
    assert False == resetpassword.checktoken(token)

def testChecktoken_VerifyTrueReturnedIfTokenExistsInForgotpassword():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    token = TestFunctions().generateTokenString(100)
    d.engine.execute(d.meta.tables["forgotpassword"].insert(), {
                         "userid": user_id,
                         "token": token,
                         "set_time": d.get_time(),
                         "link_time": 0,
                         "address": d.get_address(),
                         })
    assert resetpassword.checktoken(token)

"""
Test section for: resetpassword.py::def request(form):
"""
def testRequest_VerifyWeasylErrorLoginrecordmissingIfUsernameNotFound():
    user_name = TestFunctions().generateTestAccountName()
    email_addr = user_name + "@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'loginRecordMissing' in str(err)

def testRequest_VerifyWeasylErrorEmailinvalidIfProvidedEmailMismatchWithDBQueriedEmail():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", ["testRequest_VerifyWeasylErrorEmailinvalidIfProvidedEmailMismatchWithDBQueriedEmail@weasyl.com", user_id])
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'emailInvalid' in str(err)

def testRequest_VerifyInsertionOfForgotpasswordRowIfOtherwiseValidInfoProvided():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form)
    assert 'OSError' in str(err)
    # But we have what we need; verify token was set, both manually, and via .checktoken
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    assert 100 == len(token)
    assert resetpassword.checktoken(token)

"""
Test section for: resetpassword.py::def prepare(token):
"""
def testPrepare_VerifyDeletionOfStaleRecordsOlderThanOneHour():
    token_store =[]
    for i in range(20):
        user_name = TestFunctions().generateTestAccountName()
        user_id = db_utils.create_user(username=user_name)
        email_addr = user_name + "@weasyl.com"
        d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
        form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                   month=arrow.now().month, year=arrow.now().year)
        # Emails fail in test environments
        with pytest.raises(OSError) as err:
            resetpassword.request(form_for_request)
        assert 'OSError' in str(err)
        query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
        token = str(query[0][0])
        token_store.append(token)
    # All tokens should exist at this point
    for i in range(20):
        assert resetpassword.checktoken(token_store[i])
    # Set 5 tokens to be two hours old (0,5)
    for i in range(0,5):
        d.execute("UPDATE forgotpassword SET set_time = %i WHERE token = '%s'", [d.get_time() - 7200, token_store[i]])
    # Set 5 tokens to be 30 minutes old (5,10)
    for i in range(5,10):
        d.execute("UPDATE forgotpassword SET set_time = %i WHERE token = '%s'", [d.get_time() - 1800, token_store[i]])
    # Set 5 tokens to be 10 minutes old for the last visit time (10,15)
    for i in range(10,15):
        d.execute("UPDATE forgotpassword SET link_time = %i WHERE token = '%s'", [d.get_time() - 600, token_store[i]])
    # Set 5 tokens to be 2 minutes old for the last visit time (10,15)
    for i in range(15,20):
        d.execute("UPDATE forgotpassword SET link_time = %i WHERE token = '%s'", [d.get_time() - 120, token_store[i]])
    # This should clear all tokens >1hr old, and all tokens >5 minutes from last visit (10 total)
    resetpassword.prepare('foo')
    # This range should be cleared (set_time > 3600)
    for i in range(0,5):
        assert False == resetpassword.checktoken(token_store[i])
    # This range should still be present (set_time < 3600)
    for i in range(5,10):
        assert resetpassword.checktoken(token_store[i])
    # This range should be cleared (link_time > 300)
    for i in range(10,15):
        assert False == resetpassword.checktoken(token_store[i])
    # This range should still be present (link_time < 300
    for i in range(15,20):
        assert resetpassword.checktoken(token_store[i])

def testPrepare_VerifyUpdateOfLinktimeFieldWhenValidTokenIsPassedIn():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form_for_request)
    assert 'OSError' in str(err)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    resetpassword.prepare(token)
    query = d.execute("SELECT link_time FROM forgotpassword WHERE token = '%s'", [token])
    assert query[0][0] >= d.get_time()

"""
Test section for: resetpassword.py::def reset(form):
"""
def testReset_VerifyWeasylErrorPasswordmismatchIfPasswordsDoNotMatch():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    token = TestFunctions().generateTokenString(100)
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password='qwe', passcheck='asd')
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'passwordMismatch' in str(err)
    pass

def testReset_VerifyWeasylErrorPasswordinsecureIfPasswordConsideredInsecure():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    token = TestFunctions().generateTokenString(100)
    password = ''
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    # Considered insecure...
    for i in range(0, login._PASSWORD):
        with pytest.raises(WeasylError) as err:
            resetpassword.reset(form)
        assert 'passwordInsecure' in str(err)
        password += 'a'
        form.password = password
        form.passcheck = password
    # Considered secure...
    password += 'a'
    form.password = password
    form.passcheck = password
    # Success at WeasylError/forgotpasswordRecordMissing; we didn't make one yet
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'forgotpasswordRecordMissing' in str(err)

def testReset_VerifyWeasylErrorForgotpasswordrecordmissingIfQueryResultEmpty():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    token = TestFunctions().generateTokenString(100)
    password = '01234567890123'
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    # Technically we did this in the above test, but for completeness, target it alone
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form)
    assert 'forgotpasswordRecordMissing' in str(err)

def testReset_VerifyWeasylErrorEmailincorrectIfProvidedEmailMismatchWithDBQueriedEmail():
    # Two parts: Set forgot password record; attempt reset with incorrect email
    #  Requirement: Get token set from request()
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form_for_request)
    assert 'OSError' in str(err)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    # Force update link_time (required)
    resetpassword.prepare(token)
    email_addr_mismatch = TestFunctions().generateTestAccountName() + "@weasyl.com"
    form_for_reset = Bag(email=email_addr_mismatch, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'emailIncorrect' in str(err)

def testReset_VerifyWeasylErrorUsernameincorrectIfProvidedUsernameMismatchWithDBQueriedUsername():
    # Two parts: Set forgot password record; attempt reset with incorrect username
    #  Requirement: Get token set from request()
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form_for_request)
    assert 'OSError' in str(err)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    # Force update link_time (required)
    resetpassword.prepare(token)
    user_name_mismatch = TestFunctions().generateTestAccountName()
    form_for_reset = Bag(email=email_addr, username=user_name_mismatch, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'usernameIncorrect' in str(err)

def testReset_VerifyWeasylErrorAddressinvalidIfStoredIPAddressMismatchwithDBQueriedIP():
    # Two parts: Set forgot password record; attempt reset with incorrect IP Address in forgotpassword table vs. requesting IP
    #  Requirement: Get token set from request()
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form_for_request)
    assert 'OSError' in str(err)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    # Change IP detected when request was made (required for test)
    d.execute("UPDATE forgotpassword SET address = '%s' WHERE token = '%s'", ["127.42.42.42", token])
    # Force update link_time (required)
    resetpassword.prepare(token)
    form_for_reset = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(form_for_reset)
    assert 'addressInvalid' in str(err)

def testReset_VerifySuccessIfEverythingIsCorrect():
    # Subtests:
    #  a) Verify 'authbcrypt' table has new hash
    #  b) Verify 'forgotpassword' row is removed.
    #  > Requirement: Get token set from request()
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    email_addr = user_name + "@weasyl.com"
    d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [email_addr, user_id])
    password = '01234567890123'
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError) as err:
        resetpassword.request(form_for_request)
    assert 'OSError' in str(err)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    token = str(query[0][0])
    # Force update link_time (required)
    resetpassword.prepare(token)
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year, token=token,
               password=password, passcheck=password)
    resetpassword.reset(form)
    query = d.execute("SELECT token FROM forgotpassword WHERE userid = %i", [user_id])
    assert len(query) == 0
    query = d.execute("SELECT hashsum FROM authbcrypt WHERE userid = %i", [user_id])
    print query[0][0]
    assert bcrypt.checkpw(password.encode('utf-8'), str(query[0][0]).encode('utf-8'))

"""
Test section for: resetpassword.py::def force(userid, form):
"""
def testForce_PasswordMismatchRaisesWeasylError():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    password = '01234567890123'
    form = Bag(password=password, passcheck='1234567890987')
    with pytest.raises(WeasylError) as err:
        resetpassword.force(user_id, form)
    assert 'passwordMismatch' in str(err)

def testForce_PasswordConsideredInsecureByLengthRaisesWeasylError():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    password = ''
    for i in range(0, login._PASSWORD):
        form = Bag(password=password, passcheck=password)
        with pytest.raises(WeasylError) as err:
            resetpassword.force(user_id, form)
        assert 'passwordInsecure' in str(err)
        password += 'a'

def testForce_VerifySuccessfulExecutionOfFunction():
    user_name = TestFunctions().generateTestAccountName()
    user_id = db_utils.create_user(username=user_name)
    password = '01234567890123'
    form = Bag(password=password, passcheck=password)
    # Authbcrypt record doesn't exist; so update fails; make one
    d.execute("INSERT INTO authbcrypt VALUES (%i, '%s')", [user_id, login.passhash('passwordpassword')])
    resetpassword.force(user_id, form)
    result = login.authenticate_bcrypt(username=user_name, password=password, session=False)
    assert result == (user_id, None)

from __future__ import absolute_import

import pytest
import bcrypt

from weasyl import resetpassword, login
from weasyl import define as d
from weasyl.error import WeasylError
from weasyl.test import db_utils


user_name = "test"
email_addr = "test@weasyl.com"
token = "a" * 100


@pytest.mark.usefixtures('db')
def test_passwordMismatch_WeasylError_if_supplied_passwords_dont_match():
    db_utils.create_user(email_addr=email_addr, username=user_name)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr, username=user_name, token=token, password='qwe', passcheck='asd')
    assert 'passwordMismatch' == err.value.value


@pytest.mark.usefixtures('db')
def test_passwordInsecure_WeasylError_if_password_length_insufficient():
    db_utils.create_user(email_addr=email_addr, username=user_name)
    password = ''
    # Considered insecure...
    for i in range(0, login._PASSWORD):
        with pytest.raises(WeasylError) as err:
            resetpassword.reset(email=email_addr, username=user_name, token=token,
                                password=password, passcheck=password)
        assert 'passwordInsecure' == err.value.value
        password += 'a'
    # Considered secure...
    password += 'a'
    # Success at WeasylError/forgotpasswordRecordMissing; we didn't make one yet
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr, username=user_name, token=token, password=password, passcheck=password)
    assert 'forgotpasswordRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_forgotpasswordRecordMissing_WeasylError_if_reset_record_not_found():
    db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    # Technically we did this in the above test, but for completeness, target it alone
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr, username=user_name, token=token, password=password, passcheck=password)
    assert 'forgotpasswordRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_emailIncorrect_WeasylError_if_email_address_doesnt_match_stored_email():
    # Two parts: Set forgot password record; attempt reset with incorrect email
    #  Requirement: Get token set from request()
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    resetpassword.request(email=email_addr)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    email_addr_mismatch = "invalid-email@weasyl.com"
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr_mismatch, username=user_name, token=pw_reset_token,
                            password=password, passcheck=password)
    assert 'emailIncorrect' == err.value.value


@pytest.mark.usefixtures('db')
def test_emailIncorrect_WeasylError_if_username_doesnt_match_stored_username():
    # Two parts: Set forgot password record; attempt reset with incorrect username
    #  Requirement: Get token set from request()
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    resetpassword.request(email=email_addr)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    user_name_mismatch = "nottheaccountname123"
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr, username=user_name_mismatch, token=pw_reset_token,
                            password=password, passcheck=password)
    assert 'usernameIncorrect' == err.value.value


@pytest.mark.usefixtures('db')
def test_password_reset_fails_if_attempted_from_different_ip_address():
    # Two parts: Set forgot password record; attempt reset with incorrect IP Address in forgotpassword table vs. requesting IP
    #  Requirement: Get token set from request()
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    resetpassword.request(email=email_addr)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Change IP detected when request was made (required for test)
    d.engine.execute("UPDATE forgotpassword SET address = %(addr)s WHERE token = %(token)s",
                     addr="127.42.42.42", token=pw_reset_token)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(email=email_addr, username=user_name, token=pw_reset_token,
                            password=password, passcheck=password)
    assert 'addressInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_correct_information_supplied():
    # Subtests:
    #  a) Verify 'authbcrypt' table has new hash
    #  b) Verify 'forgotpassword' row is removed.
    #  > Requirement: Get token set from request()
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    resetpassword.request(email=email_addr)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    # Force update link_time (required)
    resetpassword.prepare(pw_reset_token)
    resetpassword.reset(email=email_addr, username=user_name, token=pw_reset_token,
                        password=password, passcheck=password)
    # 'forgotpassword' row should not exist after a successful reset
    row_does_not_exist = d.engine.execute("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    assert row_does_not_exist.first() is None
    bcrypt_hash = d.engine.scalar("SELECT hashsum FROM authbcrypt WHERE userid = %(id)s", id=user_id)
    assert bcrypt.checkpw(password.encode('utf-8'), bcrypt_hash.encode('utf-8'))

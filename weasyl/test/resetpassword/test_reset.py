from __future__ import absolute_import

import pytest
import bcrypt

from weasyl import resetpassword, login
from weasyl import define as d
from weasyl.error import WeasylError
from weasyl.test import db_utils


user_name = "test"
email_addr = "test@weasyl.com"
token = "a" * 25


@pytest.mark.usefixtures('db')
def test_passwordMismatch_WeasylError_if_supplied_passwords_dont_match():
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(
            token=token,
            password='qwe',
            passcheck='asd',
            expect_userid=user_id,
            address=None,
        )
    assert 'passwordMismatch' == err.value.value


@pytest.mark.usefixtures('db')
def test_passwordInsecure_WeasylError_if_password_length_insufficient():
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = ''
    # Considered insecure...
    for i in range(0, login._PASSWORD):
        with pytest.raises(WeasylError) as err:
            resetpassword.reset(
                token=token,
                password=password,
                passcheck=password,
                expect_userid=user_id,
                address=None,
            )
        assert 'passwordInsecure' == err.value.value
        password += 'a'
    # Considered secure...
    password += 'a'
    # Success at WeasylError/forgotpasswordRecordMissing; we didn't make one yet
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(
            token=token,
            password=password,
            passcheck=password,
            expect_userid=user_id,
            address=None,
        )
    assert 'forgotpasswordRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_forgotpasswordRecordMissing_WeasylError_if_reset_record_not_found():
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    # Technically we did this in the above test, but for completeness, target it alone
    with pytest.raises(WeasylError) as err:
        resetpassword.reset(
            token=token,
            password=password,
            passcheck=password,
            expect_userid=user_id,
            address=None,
        )
    assert 'forgotpasswordRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_correct_information_supplied(captured_tokens):
    # Subtests:
    #  a) Verify 'authbcrypt' table has new hash
    #  b) Verify 'forgotpassword' row is removed.
    #  > Requirement: Get token set from request()
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    password = '01234567890123'
    resetpassword.request(email=email_addr)
    pw_reset_token = captured_tokens[email_addr]
    resetpassword.reset(
        token=pw_reset_token,
        password=password,
        passcheck=password,
        expect_userid=user_id,
        address=None,
    )
    # 'forgotpassword' row should not exist after a successful reset
    record_count = d.engine.scalar("SELECT count(*) FROM forgotpassword")
    assert record_count == 0
    bcrypt_hash = d.engine.scalar("SELECT hashsum FROM authbcrypt WHERE userid = %(id)s", id=user_id)
    assert bcrypt.checkpw(password.encode('utf-8'), bcrypt_hash.encode('utf-8'))

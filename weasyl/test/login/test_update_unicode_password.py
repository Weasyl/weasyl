import pytest

from weasyl.test import db_utils
from weasyl import login
from weasyl.error import WeasylError


# Main test password
raw_password = "0123456789"


def test_password_and_confirmation_must_match():
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(123, '321', '123')
    assert 'passwordMismatch' == err.value.value


def test_passwords_must_be_above_minimum_length():
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(123, '012345678', '012345678')
    assert 'passwordInsecure' == err.value.value


def test_verify_correct_password_against_stored_bcrypt_hash():
    user_name = "testUpdUnicodePW001"
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    assert login.update_unicode_password(user_id, "0123456789", "0123456789") is None


def test_incorrect_passwords_raise_passwordIncorrect_WeasylError():
    user_name = "testUpdUnicodePW002"
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    with pytest.raises(WeasylError) as err:
        login.update_unicode_password(userid=user_id, password='01234567811', password_confirm='01234567811')
    assert 'passwordIncorrect' == err.value.value

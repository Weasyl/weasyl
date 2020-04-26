from __future__ import absolute_import

import pytest

from weasyl import resetpassword, login
from weasyl.error import WeasylError
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
def test_forcing_password_reset_with_mismatched_pw_fails():
    user_id = db_utils.create_user()
    password = '01234567890123'
    with pytest.raises(WeasylError) as err:
        resetpassword.force(user_id, password=password, passcheck='1234567890987')
    assert 'passwordMismatch' == err.value.value


@pytest.mark.usefixtures('db')
def test_forcing_password_reset_with_too_short_length_fails():
    # Anything under len(login._PASSWORD) characters triggers this case
    user_id = db_utils.create_user()
    password = 'shortpw'
    with pytest.raises(WeasylError) as err:
        resetpassword.force(user_id, password=password, passcheck=password)
    assert 'passwordInsecure' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_correct_information_provided():
    user_name = 'test'
    user_id = db_utils.create_user(password='passwordpassword', username=user_name)
    password = '01234567890123'
    resetpassword.force(user_id, password=password, passcheck=password)
    result = login.authenticate_bcrypt(username=user_name, password=password, request=None)
    assert result == (user_id, None)

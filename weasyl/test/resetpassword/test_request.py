"""
Test suite for: resetpassword.py::def request(form):
"""
import pytest
import arrow

from weasyl.test import db_utils
from weasyl import resetpassword
from weasyl import define as d
from weasyl.error import WeasylError


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_user_must_exist_for_a_forgotten_password_request_to_be_made():
    user_name = "test"
    email_addr = "test@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'loginRecordMissing' in str(err)


def test_email_must_match_email_stored_in_DB():
    user_name = "testrequest0002"
    email_addr = "test0001@weasyl.com"
    db_utils.create_user(email_addr=email_addr, username=user_name)
    email_addr = "invalid-email@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'emailInvalid' in str(err)


def test_verify_success_if_valid_information_provided():
    user_name = "testRequest0003"
    email_addr = "test0002@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form)
    # But we have what we need; verify token was set, both manually, and via .checktoken
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    assert 100 == len(pw_reset_token)
    assert resetpassword.checktoken(pw_reset_token)

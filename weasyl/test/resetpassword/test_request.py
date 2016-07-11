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


@pytest.mark.usefixtures('db')
def test_user_must_exist_for_a_forgotten_password_request_to_be_made():
    user_name = "test"
    email_addr = "test@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'loginRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_email_must_match_email_stored_in_DB():
    user_name = "test"
    email_addr = "test@weasyl.com"
    db_utils.create_user(email_addr=email_addr, username=user_name)
    email_addr = "invalid-email@weasyl.com"
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    with pytest.raises(WeasylError) as err:
        resetpassword.request(form)
    assert 'emailInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_valid_information_provided():
    user_name = "test"
    email_addr = "test@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    form = Bag(email=email_addr, username=user_name, day=arrow.now().day,
               month=arrow.now().month, year=arrow.now().year)
    resetpassword.request(form)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    assert 100 == len(pw_reset_token)
    assert resetpassword.checktoken(pw_reset_token)

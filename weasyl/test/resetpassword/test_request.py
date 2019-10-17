

import pytest

from weasyl import resetpassword
from weasyl import define as d
from weasyl.test import db_utils
from weasyl.test.utils import Bag


@pytest.mark.usefixtures('db')
def test_user_must_exist_for_a_forgotten_password_request_to_be_made():
    email_addr = "test@weasyl.com"
    form = Bag(email=email_addr)
    resetpassword.request(form)
    record_count = d.engine.scalar("""
        SELECT COUNT(*) FROM forgotpassword
    """)
    assert record_count == 0


@pytest.mark.usefixtures('db')
def test_email_must_match_email_stored_in_DB():
    email_addr = "test@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr)
    email_addr = "invalid-email@weasyl.com"
    form = Bag(email=email_addr)
    resetpassword.request(form)
    query = d.engine.scalar("""
        SELECT userid FROM forgotpassword WHERE userid = %(userid)s
    """, userid=user_id)
    assert not query


@pytest.mark.usefixtures('db')
def test_verify_success_if_valid_information_provided():
    email_addr = "test@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr)
    form = Bag(email=email_addr)
    resetpassword.request(form)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    assert 100 == len(pw_reset_token)
    assert resetpassword.checktoken(pw_reset_token)

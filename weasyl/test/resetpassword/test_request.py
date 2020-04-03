from __future__ import absolute_import

import pytest

from weasyl import resetpassword
from weasyl import define as d
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
def test_forgotten_password_request_always_made():
    resetpassword.request(email="test@weasyl.com")
    record_count = d.engine.scalar("SELECT count(*) FROM forgotpassword")
    assert record_count == 1


@pytest.mark.usefixtures('db')
def test_verify_success_if_valid_information_provided(captured_tokens):
    email_addr = "test@weasyl.com"
    username = "test"
    user_id = db_utils.create_user(username=username, email_addr=email_addr)
    resetpassword.request(email=email_addr)

    pw_reset_token = captured_tokens[email_addr]
    assert 25 == len(pw_reset_token)
    assert dict(resetpassword.prepare(pw_reset_token)) == {
        "userid": user_id,
        "email": email_addr,
        "username": username,
    }

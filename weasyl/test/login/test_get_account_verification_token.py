import pytest

from weasyl import login
from weasyl import define as d


user_name = "test"
email_addr = "test@weasyl.com"
token = "a" * 40

# Main test password
raw_password = "0123456789"


@pytest.mark.usefixtures('db')
def test_acct_verif_token_returned_if_email_provided_to_function():
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": user_name,
        "login_name": user_name,
        "hashpass": login.passhash(raw_password),
        "email": email_addr,
    })
    acct_verification_token = login.get_account_verification_token(email=email_addr, username=None)
    assert token == acct_verification_token


@pytest.mark.usefixtures('db')
def test_acct_verif_token_returned_if_username_provided_to_function():
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": user_name,
        "login_name": user_name,
        "hashpass": login.passhash(raw_password),
        "email": email_addr,
    })
    acct_verification_token = login.get_account_verification_token(email=None, username=user_name)
    assert token == acct_verification_token

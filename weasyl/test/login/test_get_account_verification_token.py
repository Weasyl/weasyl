"""
Test suite for: login.py::def get_account_verification_token(email=None, username=None):
"""
import arrow

from weasyl import login
from weasyl import define as d


# Main test password
raw_password = "0123456789"


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_acct_verif_token_returned_if_email_provided_to_function():
    user_name = "validuser0002"
    email_addr = "test0007@weasyl.com"
    token = "testtokentesttokentesttokentesttoken0003"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": form.username,
        "login_name": form.username,
        "hashpass": login.passhash(raw_password),
        "email": form.email,
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    acct_verification_token = login.get_account_verification_token(email=form.email, username=None)
    assert token == acct_verification_token


def test_acct_verif_token_returned_if_username_provided_to_function():
    user_name = "validuser0003"
    email_addr = "test0008@weasyl.com"
    token = "testtokentesttokentesttokentesttoken0004"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": form.username,
        "login_name": form.username,
        "hashpass": login.passhash(raw_password),
        "email": form.email,
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    acct_verification_token = login.get_account_verification_token(email=None, username=form.username)
    assert token == acct_verification_token

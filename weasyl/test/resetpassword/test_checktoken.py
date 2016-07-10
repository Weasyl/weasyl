"""
Test suite for: resetpassword.py::def checktoken(token):
"""
from weasyl.test import db_utils
from weasyl import resetpassword
from weasyl import define as d


def test_false_returned_if_token_does_not_exist():
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000000"
    assert not resetpassword.checktoken(token)


def test_true_returned_if_token_exists():
    user_id = db_utils.create_user(username='checktoken0002')
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000001"
    d.engine.execute(d.meta.tables["forgotpassword"].insert(), {
        "userid": user_id,
        "token": token,
        "set_time": d.get_time(),
        "link_time": 0,
        "address": d.get_address(),
    })
    assert resetpassword.checktoken(token)

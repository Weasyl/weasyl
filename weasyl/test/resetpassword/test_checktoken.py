

import pytest

from weasyl import resetpassword
from weasyl import define as d
from weasyl.test import db_utils


def test_false_returned_if_token_does_not_exist():
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000000"
    assert not resetpassword.checktoken(token)


@pytest.mark.usefixtures('db')
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

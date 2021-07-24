import hashlib

import pytest

from weasyl import resetpassword
from weasyl import define as d
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
def test_none_returned_if_token_does_not_exist():
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000000"
    assert resetpassword.prepare(token) is None


@pytest.mark.usefixtures('db')
def test_user_info_returned_if_token_exists():
    email_addr = "test@weasyl.com"
    username = "checktoken0002"
    user_id = db_utils.create_user(username=username, email_addr=email_addr)
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000008"
    d.engine.execute(d.meta.tables["forgotpassword"].insert(), {
        "userid": user_id,
        "token_sha256": hashlib.sha256(token.encode("ascii")).digest(),
        "email": email_addr,
    })
    assert dict(resetpassword.prepare(token)) == {
        "userid": user_id,
        "email": email_addr,
        "username": username,
    }


@pytest.mark.usefixtures('db')
def test_unregistered():
    email_addr = "test@weasyl.com"
    user_id = db_utils.create_user(username='checktoken0002')
    token = "testtokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentesttokentest000008"
    d.engine.execute(d.meta.tables["forgotpassword"].insert(), {
        "userid": user_id,
        "token_sha256": hashlib.sha256(token.encode("ascii")).digest(),
        "email": email_addr,
    })
    assert resetpassword.prepare(token) == resetpassword.Unregistered(email=email_addr)


@pytest.mark.usefixtures('db')
def test_stale_records_get_deleted_when_function_is_called(captured_tokens):
    email_addrs = list(map("test{}@weasyl.com".format, range(10)))

    for email_addr in email_addrs:
        db_utils.create_user(email_addr=email_addr)
        resetpassword.request(email=email_addr)
    # Set 5 tokens to be two hours old (0,5)
    for i in range(0, 5):
        d.engine.execute("UPDATE forgotpassword SET created_at = now() - INTERVAL '2 hours' WHERE email = %(email)s",
                         email=email_addrs[i])
    # Set 5 tokens to be 30 minutes old (5,10)
    for i in range(5, 10):
        d.engine.execute("UPDATE forgotpassword SET created_at = now() - INTERVAL '30 minutes' WHERE email = %(email)s",
                         email=email_addrs[i])
    # This range should be invalid (created_at > 3600)
    for i in range(0, 5):
        assert not resetpassword.prepare(captured_tokens[email_addrs[i]])
    # This range should still be valid (created_at < 3600)
    for i in range(5, 10):
        assert resetpassword.prepare(captured_tokens[email_addrs[i]])

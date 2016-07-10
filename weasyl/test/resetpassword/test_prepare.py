import pytest
import arrow

from weasyl.test import db_utils
from weasyl import resetpassword
from weasyl import define as d


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_stale_records_get_deleted_when_function_is_called():
    token_store = []
    for i in range(20):
        user_name = "testPrepare%d" % (i,)
        email_addr = "test%d@weasyl.com" % (i,)
        user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
        form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                               month=arrow.now().month, year=arrow.now().year)
        # Emails fail in test environments
        with pytest.raises(OSError):
            resetpassword.request(form_for_request)
        pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
        token_store.append(pw_reset_token)
    # All tokens should exist at this point
    for i in range(20):
        assert resetpassword.checktoken(token_store[i])
    # Set 5 tokens to be two hours old (0,5) (7200)
    for i in range(0, 5):
        d.engine.execute("UPDATE forgotpassword SET set_time = %(time)s WHERE token = %(token)s",
                         time=d.get_time() - 7200, token=token_store[i])
    # Set 5 tokens to be 30 minutes old (5,10) (1800)
    for i in range(5, 10):
        d.engine.execute("UPDATE forgotpassword SET set_time = %(time)s WHERE token = %(token)s",
                         time=d.get_time() - 1800, token=token_store[i])
    # Set 5 tokens to be 10 minutes old for the last visit time (10,15) (600)
    for i in range(10, 15):
        d.engine.execute("UPDATE forgotpassword SET link_time = %(time)s WHERE token = %(token)s",
                         time=d.get_time() - 600, token=token_store[i])
    # Set 5 tokens to be 2 minutes old for the last visit time (10,15) (120)
    for i in range(15, 20):
        d.engine.execute("UPDATE forgotpassword SET link_time = %(time)s WHERE token = %(token)s",
                         time=d.get_time() - 120, token=token_store[i])
    # This should clear all tokens >1hr old, and all tokens >5 minutes from last visit (10 total)
    resetpassword.prepare('foo')
    # This range should be cleared (set_time > 3600)
    for i in range(0, 5):
        assert not resetpassword.checktoken(token_store[i])
    # This range should still be present (set_time < 3600)
    for i in range(5, 10):
        assert resetpassword.checktoken(token_store[i])
    # This range should be cleared (link_time > 300)
    for i in range(10, 15):
        assert not resetpassword.checktoken(token_store[i])
    # This range should still be present (link_time < 300)
    for i in range(15, 20):
        assert resetpassword.checktoken(token_store[i])


def test_link_time_field_is_updated_when_valid_token_supplied_to_function():
    user_name = "testPrepareFunc002"
    email_addr = "test0003@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    # Emails fail in test environments
    with pytest.raises(OSError):
        resetpassword.request(form_for_request)
    pw_reset_token = d.engine.scalar("SELECT token FROM forgotpassword WHERE userid = %(id)s", id=user_id)
    resetpassword.prepare(pw_reset_token)
    link_time = d.engine.scalar("SELECT link_time FROM forgotpassword WHERE token = %(token)s", token=pw_reset_token)
    assert link_time >= d.get_time()

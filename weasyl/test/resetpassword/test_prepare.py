from __future__ import absolute_import

import pytest
import arrow

from weasyl import resetpassword
from weasyl import define as d
from weasyl.test import db_utils
from weasyl.test.utils import Bag


@pytest.mark.usefixtures('db')
def test_stale_records_get_deleted_when_function_is_called():
    token_store = []
    for i in range(20):
        user_name = "testPrepare%d" % (i,)
        email_addr = "test%d@weasyl.com" % (i,)
        user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
        form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                               month=arrow.now().month, year=arrow.now().year)
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


@pytest.mark.usefixtures('db')
def test_link_time_field_is_updated_when_valid_token_supplied_to_function():
    user_name = "test"
    email_addr = "test@weasyl.com"
    user_id = db_utils.create_user(email_addr=email_addr, username=user_name)
    form_for_request = Bag(email=email_addr, username=user_name, day=arrow.now().day,
                           month=arrow.now().month, year=arrow.now().year)
    resetpassword.request(form_for_request)

    query = d.engine.execute("""
        SELECT token, link_time FROM forgotpassword WHERE userid = %(id)s
    """, id=user_id).first()
    d.engine.execute("""
        UPDATE forgotpassword
        SET link_time = %(link_time)s
        WHERE token = %(token)s
    """, link_time=query['link_time'] - 10, token=query['token'])

    resetpassword.prepare(query['token'])
    link_time = d.engine.scalar("SELECT link_time FROM forgotpassword WHERE token = %(token)s", token=query['token'])
    # The current link_time is not going to be the same as when we previously got it
    assert link_time != query['link_time']
    # The link_time will be less than or equal to the current time.
    assert link_time <= d.get_time()
    # And it will also be greater than or equal to the original value.
    assert link_time >= query['link_time']

"""
Test suite for: login.py::def signin(userid):
"""
import pytest

from weasyl.test import db_utils
from weasyl import login
from weasyl import define as d


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_verify_login_record_is_updated():
    user_id = db_utils.create_user()
    d.engine.execute("UPDATE login SET last_login = -1 WHERE userid = %(id)s", id=user_id)
    # login.signin(user_id) -will- raise an AttributeError when d.web.ctx.weasyl_session
    #   tries to execute itself; so catch/handle; it's a test environment issue
    with pytest.raises(AttributeError) as err:
        login.signin(user_id)
    print str(err)
    last_login = d.engine.scalar("SELECT last_login FROM login WHERE userid = %(id)s", id=user_id)
    assert last_login > -1

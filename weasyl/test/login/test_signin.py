from __future__ import absolute_import

import pytest

from pyramid.threadlocal import get_current_request

from weasyl import login
from weasyl import define as d
from weasyl.test import db_utils
from weasyl.test.utils import Bag


@pytest.mark.usefixtures('db')
def test_verify_login_record_is_updated():
    # Use a fake session for this test.
    get_current_request().weasyl_session = Bag()
    user_id = db_utils.create_user()
    d.engine.execute("UPDATE login SET last_login = -1 WHERE userid = %(id)s", id=user_id)
    login.signin(user_id)
    last_login = d.engine.scalar("SELECT last_login FROM login WHERE userid = %(id)s", id=user_id)
    assert last_login > -1

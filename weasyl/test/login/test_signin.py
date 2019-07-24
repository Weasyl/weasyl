from __future__ import absolute_import

import pytest

from pyramid.threadlocal import get_current_request

from weasyl import login
from weasyl import define as d
from weasyl.sessions import create_session
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
def test_verify_login_record_is_updated():
    # Use a fake session for this test.
    user_id = db_utils.create_user()
    sess = get_current_request().weasyl_session = create_session(user_id)
    db = d.connect()
    db.add(sess)
    db.flush()
    d.engine.execute("UPDATE login SET last_login = -1 WHERE userid = %(id)s", id=user_id)
    login.signin(get_current_request(), user_id)
    last_login = d.engine.scalar("SELECT last_login FROM login WHERE userid = %(id)s", id=user_id)
    assert last_login > -1

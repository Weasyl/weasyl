from datetime import datetime, timezone
import pytest

from pyramid.threadlocal import get_current_request

from weasyl import login
from weasyl import define as d
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
def test_verify_login_record_is_updated():
    # Use a fake session for this test.
    user_id = db_utils.create_user()
    get_current_request().weasyl_session = None
    time = datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc)  # Arbitrary date that should be earlier than now.
    d.engine.execute("UPDATE login SET last_login = %(timestamp)s WHERE userid = %(id)s", id=user_id, timestamp=time)
    login.signin(get_current_request(), user_id)
    last_login = d.engine.scalar("SELECT last_login FROM login WHERE userid = %(id)s", id=user_id)
    assert last_login > time

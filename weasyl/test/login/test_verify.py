from __future__ import absolute_import, unicode_literals

import pytest
import arrow

from weasyl import login
from weasyl import define as d
from weasyl.error import WeasylError


token = "a" * 40
username = "test"
email = 'test@weasyl.com'


def _create_pending_account(invalid=False):
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": username,
        "login_name": username,
        "hashpass": login.passhash('0123456789'),
        "email": email,
        "birthday": arrow.Arrow(2000, 1, 1).datetime,
        "created_at": arrow.now().datetime,
        "invalid": invalid,
    })


@pytest.mark.usefixtures('db')
def test_error_raised_if_invalid_token_provided_to_function():
    with pytest.raises(WeasylError) as err:
        login.verify("qwe")
    assert 'logincreateRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_plausible_deniability_invalid_logincreate_record_does_not_create():
    """
    A logincreate record with the 'invalid' field set should not create the account.
    Expected result is a `raise WeasylError("logincreateRecordMissing")`
    """
    _create_pending_account(invalid=True)

    with pytest.raises(WeasylError) as err:
        login.verify(token)
    assert 'logincreateRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_valid_token_provided():
    _create_pending_account()
    login.verify(token)

    userid = d.engine.scalar("SELECT userid FROM login WHERE login_name = %(name)s", name=username)
    # Verify that each table gets the correct information added to it (checks for record's existence for brevity)
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM authbcrypt WHERE userid = %(userid)s)",
        userid=userid)
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM profile WHERE userid = %(userid)s)",
        userid=userid)
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM userinfo WHERE userid = %(userid)s)",
        userid=userid)
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM welcomecount WHERE userid = %(userid)s)",
        userid=userid)

    # The 'logincreate' record gets deleted on successful execution; verify this
    assert not d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM logincreate WHERE token = %(token)s)",
        token=token)

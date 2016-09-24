from __future__ import absolute_import

import arrow
import pytest
import web

from weasyl import login
from weasyl import define as d
from weasyl.error import WeasylError


token = "a" * 40


@pytest.mark.usefixtures('db')
def test_error_raised_if_invalid_token_provided_to_function():
    with pytest.raises(WeasylError) as err:
        login.verify("qwe")
    assert 'logincreateRecordMissing' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_success_if_valid_token_provided():
    form = web.Storage(username=u'test', password=u'0123456789', passcheck=u'0123456789',
                       email=u'test@weasyl.com', emailcheck=u'test@weasyl.com',
                       day=u'12', month=u'12', year=u'%d' % (arrow.now().year - 19,))
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": form.username,
        "login_name": form.username,
        "hashpass": login.passhash(u'0123456789'),
        "email": form.email,
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    login.verify(token)

    userid = d.engine.scalar("SELECT userid FROM login WHERE login_name = %(name)s", name=form.username)
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
        "SELECT EXISTS (SELECT 0 FROM userstats WHERE userid = %(userid)s)",
        userid=userid)
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM welcomecount WHERE userid = %(userid)s)",
        userid=userid)

    # The 'logincreate' record gets deleted on successful execution; verify this
    assert not d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM logincreate WHERE token = %(token)s)",
        token=token)

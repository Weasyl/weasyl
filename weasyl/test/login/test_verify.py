import pytest
import arrow

from weasyl import login
from weasyl import define as d
from weasyl.error import WeasylError


# Main test password
raw_password = "0123456789"


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_error_raised_if_invalid_token_provided_to_function():
    with pytest.raises(WeasylError) as err:
        login.verify("qwe")
    assert 'logincreateRecordMissing' == err.value.value


def test_verify_success_if_valid_token_provided():
    user_name = "validuser0004"
    email_addr = "test0006@weasyl.com"
    token = "testtokentesttokentesttokentesttoken0002"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": form.username,
        "login_name": form.username,
        "hashpass": login.passhash(raw_password),
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

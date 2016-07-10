import pytest
import arrow

from weasyl.test import db_utils
from weasyl import login
from weasyl import define as d
from weasyl.error import WeasylError


# Main test password
raw_password = "0123456789"


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_DMY_not_integer_raises_birthdayInvalid_WeasylError():
    user_name = "test"
    # Check for failure state if 'day' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='test', month='31', year='1942')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'month' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='test', year='1942')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an integer, e.g., string
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='31', year='test')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value


def test_DMY_out_of_valid_ranges_raises_birthdayInvalid_WeasylError():
    user_name = "test"
    # Check for failure state if 'day' is not an valid day e.g., 42
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='42', month='12', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'month' is not an valid month e.g., 42
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='42', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year='-1')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value


def test_DMY_missing_raises_birthdayInvalid_WeasylError():
    user_name = "test"
    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day=None, month='12', year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month=None, year='2000')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an valid year e.g., -1
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year=None)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value


def test_under_13_age_raises_birthdayInvalid_WeasylError():
    user_name = "test"
    # Check for failure state if computed birthday is <13 years old
    form = Bag(username=user_name, password='', passcheck='',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year=arrow.now().year - 11)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value


def test_passwords_must_match():
    user_name = "test"
    # Check for failure if password != passcheck
    form = Bag(username=user_name, password='123', passcheck='qwe',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'passwordMismatch' == err.value.value


def test_passwords_must_be_of_sufficient_length():
    user_name = "test"
    password = "tooShort"
    form = Bag(username=user_name, password=password, passcheck=password,
               email='foo', emailcheck='foo',
               day='12', month='12', year=arrow.now().year - 19)
    # Insecure length
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'passwordInsecure' == err.value.value
    # Secure length
    password = "thisIsAcceptable"
    form.passcheck = form.password = password
    # emailInvalid is the next failure state after passwordInsecure, so it is a 'success' for this testcase
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' == err.value.value


def test_create_fails_if_email_and_emailcheck_dont_match():
    user_name = "test"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email='test@weasyl.com', emailcheck='testt@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailMismatch' == err.value.value


def test_create_fails_if_email_is_invalid():
    user_name = "test"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=';--', emailcheck=';--',
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' == err.value.value


def test_create_fails_if_another_account_has_email_linked_to_their_account():
    """
    Test checks to see if an email is tied to an active user account. If so,
    login.create() will not permit another account to be made for the same
    address.
    """
    user_name = "emailexistsinlogin"
    email_addr = "test0001@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    db_utils.create_user(username=user_name, email_addr=email_addr)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailExists' == err.value.value


def test_create_fails_if_pending_account_has_same_email():
    """
    Test checks to see if an email is tied to a pending account creation entry
    in logincreate. If so, login.create() will not permit another account to be
    made for the same address.
    """
    user_name = "EmailExLoginCreate001"
    user_name_2 = "EmailExLoginCreate002"
    email_addr = "test0002@weasyl.com"
    token = "testtokentesttokentesttokentesttoken0000"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": user_name_2,
        "login_name": user_name_2,
        "hashpass": login.passhash(raw_password),
        "email": email_addr,
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailExists' == err.value.value


def test_username_cant_be_blank_or_have_semicolon():
    email_addr = "test@weasyl.com"
    form = Bag(username='...', password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameInvalid' == err.value.value
    form.username = 'testloginsuite;'
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameInvalid' == err.value.value


def test_create_fails_if_username_is_a_prohibited_name():
    form = Bag(username='testloginsuite', password='0123456789', passcheck='0123456789',
               email='test@weasyl.com', emailcheck='test@weasyl.com',
               day='12', month='12', year=arrow.now().year - 19)
    prohibited_names = ["admin", "administrator", "mod", "moderator", "weasyl",
                        "weasyladmin", "weasylmod", "staff", "security"]
    for name in prohibited_names:
        form.username = name
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'usernameInvalid' == err.value.value


def test_usernames_must_be_unique():
    user_name = "usernameexists0001"
    email_addr = "test@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    db_utils.create_user(username=user_name, email_addr="test_2@weasyl.com")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


def test_usernames_cannot_match_pending_account_usernames():
    user_name = "usernameexists0002"
    email_addr = "test@weasyl.com"
    token = "testtokentesttokentesttokentesttoken0001"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": token,
        "username": user_name,
        "login_name": user_name,
        "hashpass": login.passhash(raw_password),
        "email": "test0003@weasyl.com",
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


def test_username_cannot_match_an_active_alias():
    user_name = "usernameexists0003"
    email_addr = "test0004@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    user_id = db_utils.create_user(username='aliastest')
    d.engine.execute("INSERT INTO useralias VALUES (%(userid)s, %(username)s, 'p')", userid=user_id, username=user_name)
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


def test_verify_correct_information_creates_account():
    user_name = "validuser0001"
    email_addr = "test0005@weasyl.com"
    form = Bag(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    # Emailing doesn't work in the test environment, but by this point the
    # logincreate entry has been made
    with pytest.raises(OSError):
        login.create(form)
    # This record should exist when this function completes successfully
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)",
        name=form.username)

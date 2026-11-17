import pytest
from web.utils import Storage as Bag

from weasyl import define as d
from weasyl import login
from weasyl.error import WeasylError
from weasyl.test import db_utils


user_name = "test"
email_addr = "test@weasyl.com"

# Main test password
raw_password = "0123456789"


@pytest.mark.usefixtures('db')
def test_age_minimum():
    form = Bag(username=user_name, password='',
               email='test@weasyl.com')
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'birthdayInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_passwords_must_be_of_sufficient_length():
    password = "tooShort"
    form = Bag(username=user_name, password=password,
               email='foo',
               age="13+")
    # Insecure length
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'passwordInsecure' == err.value.value
    # Secure length
    password = "thisIsAcceptable"
    form.password = password
    # emailInvalid is the next failure state after passwordInsecure, so it is a 'success' for this testcase
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_create_fails_if_email_is_invalid():
    form = Bag(username=user_name, password='0123456789',
               email=';--',
               age="13+")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'emailInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_create_fails_if_another_account_has_email_linked_to_their_account():
    """
    Test checks to see if an email is tied to an active user account. If so,
    login.create() will not permit another account to be made for the same
    address.
    """
    db_utils.create_user(username=user_name, email_addr=email_addr)
    form = Bag(username="user", password='0123456789',
               email=email_addr,
               age="13+")
    login.create(form)
    query = d.engine.scalar("""
        SELECT username FROM logincreate WHERE username = %(username)s AND invalid IS TRUE
    """, username=form.username)
    assert query == "user"


@pytest.mark.usefixtures('db')
def test_create_fails_if_pending_account_has_same_email():
    """
    Test checks to see if an email is tied to a pending account creation entry
    in logincreate. If so, login.create() will not permit another account to be
    made for the same address.
    """
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": 40 * "a",
        "username": "existing",
        "login_name": "existing",
        "hashpass": login.passhash(raw_password),
        "email": email_addr,
    })
    form = Bag(username="test", password='0123456789',
               email=email_addr,
               age="13+")
    login.create(form)
    query = d.engine.scalar("""
        SELECT username FROM logincreate WHERE username = %(username)s AND invalid IS TRUE
    """, username=form.username)
    assert query == "test"


@pytest.mark.usefixtures('db')
def test_username_cant_be_blank_or_have_semicolon():
    form = Bag(username='...', password='0123456789',
               email=email_addr,
               age="13+")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameInvalid' == err.value.value
    form.username = 'testloginsuite;'
    login.create(form)
    assert d.engine.scalar(
        "SELECT username FROM logincreate WHERE email = %(email)s LIMIT 1",
        email=form.email,
    ) == "testloginsuite"


@pytest.mark.usefixtures('db')
def test_create_fails_if_username_is_a_prohibited_name():
    form = Bag(username='testloginsuite', password='0123456789',
               email='test@weasyl.com',
               age="13+")
    prohibited_names = ["admin", "administrator", "mod", "moderator", "weasyl",
                        "weasyladmin", "weasylmod", "staff", "security"]
    for name in prohibited_names:
        form.username = name
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'usernameBanned' == err.value.value


@pytest.mark.usefixtures('db')
def test_usernames_must_be_unique():
    db_utils.create_user(username=user_name, email_addr="test_2@weasyl.com")
    form = Bag(username=user_name, password='0123456789',
               email=email_addr,
               age="13+")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_usernames_cannot_match_pending_account_usernames():
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": 40 * "a",
        "username": user_name,
        "login_name": user_name,
        "hashpass": login.passhash(raw_password),
        "email": "test0003@weasyl.com",
    })
    form = Bag(username=user_name, password='0123456789',
               email=email_addr,
               age="13+")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_username_cannot_match_an_active_alias():
    user_id = db_utils.create_user(username='aliastest')
    d.engine.execute("INSERT INTO useralias VALUES (%(userid)s, %(username)s, 'p')", userid=user_id, username=user_name)
    form = Bag(username=user_name, password='0123456789',
               email=email_addr,
               age="13+")
    with pytest.raises(WeasylError) as err:
        login.create(form)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_correct_information_creates_account():
    form = Bag(username=user_name, password='0123456789',
               email=email_addr,
               age="13+")
    login.create(form)
    # This record should exist when this function completes successfully
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)",
        name=form.username)


class TestAccountCreationBlacklist:
    @pytest.mark.usefixtures('db')
    def test_create_fails_if_email_domain_is_blacklisted(self):
        blacklisted_email = "test@blacklisted.example"
        form = Bag(username=user_name, password='0123456789',
                   email=blacklisted_email,
                   age="13+")
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'emailBlacklisted' == err.value.value

    @pytest.mark.usefixtures('db')
    def test_verify_subdomains_of_blocked_sites_blocked(self):
        blacklisted_email = "test@subdomain.blacklisted.example"
        form = Bag(username=user_name, password='0123456789',
                   email=blacklisted_email,
                   age="13+")
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'emailBlacklisted' == err.value.value

        blacklisted_email = "test@deeper.subdomain.blacklisted.example"
        form = Bag(username=user_name, password='0123456789',
                   email=blacklisted_email,
                   age="13+")
        with pytest.raises(WeasylError) as err:
            login.create(form)
        assert 'emailBlacklisted' == err.value.value

    @pytest.mark.usefixtures('db')
    def test_similarly_named_domains_are_not_blocked(self):
        mail = "test@notblacklisted.example"
        form = Bag(username=user_name, password='0123456789',
                   email=mail,
                   age="13+")
        login.create(form)

        mail = "test@also.notblacklisted.example"
        form = Bag(username=user_name + "1", password='0123456789',
                   email=mail,
                   age="13+")
        login.create(form)

        mail = "test@blacklisted.example.notblacklisted.example"
        form = Bag(username=user_name + "2", password='0123456789',
                   email=mail,
                   age="13+")
        login.create(form)

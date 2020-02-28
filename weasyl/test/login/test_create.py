from __future__ import absolute_import

import pytest
import arrow

from weasyl import define as d
from weasyl import login
from weasyl.error import WeasylError
from weasyl.test import db_utils


user_name = "test"
email_addr = "test@weasyl.com"

# Main test password
raw_password = "0123456789"


@pytest.mark.usefixtures('db')
def test_DMY_not_integer_raises_birthdayInvalid_WeasylError():
    # Check for failure state if 'day' is not an integer, e.g., string
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='test', month='31', year='1942')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'month' is not an integer, e.g., string
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='test', year='1942')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an integer, e.g., string
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='31', year='test')
    assert 'birthdayInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_DMY_out_of_valid_ranges_raises_birthdayInvalid_WeasylError():
    # Check for failure state if 'day' is not an valid day e.g., 42
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='42', month='12', year='2000')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'month' is not an valid month e.g., 42
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='42', year='2000')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an valid year e.g., -1
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='12', year='-1')
    assert 'birthdayInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_DMY_missing_raises_birthdayInvalid_WeasylError():
    # Check for failure state if 'day' is not an valid year e.g., None
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day=None, month='12', year='2000')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'month' is not an valid month e.g., None
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month=None, year='2000')
    assert 'birthdayInvalid' == err.value.value

    # Check for failure state if 'year' is not an valid year e.g., None
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='12', year=None)
    assert 'birthdayInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_under_13_age_raises_birthdayInvalid_WeasylError():
    # Check for failure state if computed birthday is <13 years old
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='', passcheck='',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='12', year=arrow.now().year - 11)
    assert 'birthdayInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_passwords_must_match():
    # Check for failure if password != passcheck
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='123', passcheck='qwe',
                     email='test@weasyl.com', emailcheck='test@weasyl.com',
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'passwordMismatch' == err.value.value


@pytest.mark.usefixtures('db')
def test_passwords_must_be_of_sufficient_length():
    password = "tooShort"
    # Insecure length
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password=password, passcheck=password,
                     email='foo', emailcheck='foo',
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'passwordInsecure' == err.value.value
    # Secure length
    password = "thisIsAcceptable"
    # emailInvalid is the next failure state after passwordInsecure, so it is a 'success' for this testcase
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password=password, passcheck=password,
                     email='foo', emailcheck='foo',
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'emailInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_create_fails_if_email_and_emailcheck_dont_match():
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email='test@weasyl.com', emailcheck='testt@weasyl.com',
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'emailMismatch' == err.value.value


@pytest.mark.usefixtures('db')
def test_create_fails_if_email_is_invalid():
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email=';--', emailcheck=';--',
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'emailInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_create_fails_if_another_account_has_email_linked_to_their_account():
    """
    Test checks to see if an email is tied to an active user account. If so,
    login.create() will not permit another account to be made for the same
    address.
    """
    db_utils.create_user(username=user_name, email_addr=email_addr)
    login.create(username="user", password='0123456789', passcheck='0123456789',
                 email=email_addr, emailcheck=email_addr,
                 day='12', month='12', year=arrow.now().year - 19)
    query = d.engine.scalar("""
        SELECT username FROM logincreate WHERE username = %(username)s AND invalid IS TRUE
    """, username='user')
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
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    username = 'test'
    login.create(username=username, password='0123456789', passcheck='0123456789',
                 email=email_addr, emailcheck=email_addr,
                 day='12', month='12', year=arrow.now().year - 19)
    query = d.engine.scalar("""
        SELECT username FROM logincreate WHERE username = %(username)s AND invalid IS TRUE
    """, username=username)
    assert query == "test"


@pytest.mark.usefixtures('db')
def test_username_cant_be_blank_or_have_semicolon():
    with pytest.raises(WeasylError) as err:
        login.create(username='', password='0123456789', passcheck='0123456789',
                     email=email_addr, emailcheck=email_addr,
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'usernameInvalid' == err.value.value
    login.create(username='testloginsuite;', password='0123456789', passcheck='0123456789',
                 email=email_addr, emailcheck=email_addr,
                 day='12', month='12', year=arrow.now().year - 19)
    assert d.engine.scalar(
        "SELECT username FROM logincreate WHERE email = %(email)s LIMIT 1",
        email=form.email,
    ) == "testloginsuite"


@pytest.mark.usefixtures('db')
def test_create_fails_if_username_is_a_prohibited_name():
    prohibited_names = ["admin", "administrator", "mod", "moderator", "weasyl",
                        "weasyladmin", "weasylmod", "staff", "security"]
    for name in prohibited_names:
        with pytest.raises(WeasylError) as err:
            login.create(username=name, password='0123456789', passcheck='0123456789',
                         email='test@weasyl.com', emailcheck='test@weasyl.com',
                         day='12', month='12', year=arrow.now().year - 19)
        assert 'usernameInvalid' == err.value.value


@pytest.mark.usefixtures('db')
def test_usernames_must_be_unique():
    db_utils.create_user(username=user_name, email_addr="test_2@weasyl.com")
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email=email_addr, emailcheck=email_addr,
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_usernames_cannot_match_pending_account_usernames():
    d.engine.execute(d.meta.tables["logincreate"].insert(), {
        "token": 40 * "a",
        "username": user_name,
        "login_name": user_name,
        "hashpass": login.passhash(raw_password),
        "email": "test0003@weasyl.com",
        "birthday": arrow.Arrow(2000, 1, 1),
        "unixtime": arrow.now(),
    })
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email=email_addr, emailcheck=email_addr,
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_username_cannot_match_an_active_alias():
    user_id = db_utils.create_user(username='aliastest')
    d.engine.execute("INSERT INTO useralias VALUES (%(userid)s, %(username)s, 'p')", userid=user_id, username=user_name)
    with pytest.raises(WeasylError) as err:
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email=email_addr, emailcheck=email_addr,
                     day='12', month='12', year=arrow.now().year - 19)
    assert 'usernameExists' == err.value.value


@pytest.mark.usefixtures('db')
def test_verify_correct_information_creates_account():
    login.create(username=user_name, password='0123456789', passcheck='0123456789',
               email=email_addr, emailcheck=email_addr,
               day='12', month='12', year=arrow.now().year - 19)
    # This record should exist when this function completes successfully
    assert d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)",
        name=user_name)


class TestAccountCreationBlacklist(object):
    @pytest.mark.usefixtures('db')
    def test_create_fails_if_email_domain_is_blacklisted(self):
        """
        Test verifies that login.create() will properly fail to register new accounts
        when the domain portion of the email address is contained in the emailblacklist
        table.
        """
        d.engine.execute(d.meta.tables["emailblacklist"].insert(), {
            "domain_name": "blacklisted.com",
            "reason": "test case for login.create()",
            "added_by": db_utils.create_user(),
        })
        blacklisted_email = "test@blacklisted.com"
        with pytest.raises(WeasylError) as err:
            login.create(username=user_name, password='0123456789', passcheck='0123456789',
                         email=blacklisted_email, emailcheck=blacklisted_email,
                         day='12', month='12', year=arrow.now().year - 19)
        assert 'emailBlacklisted' == err.value.value

    @pytest.mark.usefixtures('db')
    def test_verify_subdomains_of_blocked_sites_blocked(self):
        """
        Blacklisted: badsite.net
        Blocked: badsite.net
        Also blocked: subdomain.badsite.net
        """
        d.engine.execute(d.meta.tables["emailblacklist"].insert(), {
            "domain_name": "blacklisted.com",
            "reason": "test case for login.create()",
            "added_by": db_utils.create_user(),
        })
        # Test the domains from the emailblacklist table
        blacklisted_email = "test@subdomain.blacklisted.com"
        with pytest.raises(WeasylError) as err:
            login.create(username=user_name, password='0123456789', passcheck='0123456789',
                         email=blacklisted_email, emailcheck=blacklisted_email,
                         day='12', month='12', year=arrow.now().year - 19)
        assert 'emailBlacklisted' == err.value.value

        # Test the domains from the code that would download the list of disposable domains
        blacklisted_email = "test@mail.sub.sharklasers.com"
        with pytest.raises(WeasylError) as err:
            login.create(username=user_name, password='0123456789', passcheck='0123456789',
                         email=blacklisted_email, emailcheck=blacklisted_email,
                         day='12', month='12', year=arrow.now().year - 19)
        assert 'emailBlacklisted' == err.value.value

        # Ensure address in the form of <domain.domain> is blocked
        blacklisted_email = "test@sharklasers.com.sharklasers.com"
        with pytest.raises(WeasylError) as err:
            login.create(username=user_name, password='0123456789', passcheck='0123456789',
                         email=blacklisted_email, emailcheck=blacklisted_email,
                         day='12', month='12', year=arrow.now().year - 19)
        assert 'emailBlacklisted' == err.value.value

    @pytest.mark.usefixtures('db')
    def test_similarly_named_domains_are_not_blocked(self):
        """
        Blacklisted: badsite.net
        /Not/ Blocked: notabadsite.net
        Also /Not/ blocked: subdomain.notabadsite.net
        """
        d.engine.execute(d.meta.tables["emailblacklist"].insert(), {
            "domain_name": "blacklisted.com",
            "reason": "test case for login.create()",
            "added_by": db_utils.create_user(),
        })
        mail = "test@notblacklisted.com"
        login.create(username=user_name, password='0123456789', passcheck='0123456789',
                     email=mail, emailcheck=mail,
                     day='12', month='12', year=arrow.now().year - 19)

        mail = "test@also.notblacklisted.com"
        login.create(username=user_name + "1", password='0123456789', passcheck='0123456789',
                     email=mail, emailcheck=mail,
                     day='12', month='12', year=arrow.now().year - 19)

        mail = "test@blacklisted.com.notblacklisted.com"
        login.create(username=user_name + "2", password='0123456789', passcheck='0123456789',
                     email=mail, emailcheck=mail,
                     day='12', month='12', year=arrow.now().year - 19)

import arrow
import pytest
import unittest

from weasyl import define as d
from weasyl import profile
from weasyl.error import WeasylError
from weasyl.test import db_utils


def _exchange_settings_from_settings_string(settings_string):
    """
    Given a (terrible and brittle) exchange settings string from a user profile,
    returns a dict of their exchange settings.
    """
    return {
        profile.EXCHANGE_TYPE_COMMISSION: profile.EXCHANGE_SETTING_CODE_MAP[settings_string[0]],
        profile.EXCHANGE_TYPE_TRADE: profile.EXCHANGE_SETTING_CODE_MAP[settings_string[1]],
        profile.EXCHANGE_TYPE_REQUEST: profile.EXCHANGE_SETTING_CODE_MAP[settings_string[2]],
    }


@pytest.mark.usefixtures('db')
class ProfileManageTestCase(unittest.TestCase):
    def setUp(self):
        self.mod = db_utils.create_user()

    def test_select_manage(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:support@weasyl.com',
            },
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        test_user_profile = profile.select_manage(user)
        self.assertEqual(len(test_user_profile['sorted_user_links']), 2)

    def test_remove_social_links(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:support@weasyl.com',
            },
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        profile.do_manage(self.mod, user, remove_social=['Email'])

        test_user_profile = profile.select_manage(user)
        self.assertEqual(test_user_profile['sorted_user_links'], [('Twitter', ['Weasyl'])])

    def test_sort_user_links(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:sysop@weasyl.com',
            },
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'WeasylDev',
            }
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        test_user_profile = profile.select_manage(user)
        self.assertEqual(test_user_profile['sorted_user_links'], [
            ('Email', ['mailto:sysop@weasyl.com']),
            ('Twitter', ['Weasyl', 'WeasylDev']),
        ])

    def test_valid_commission_settings(self):
        user = db_utils.create_user()

        profile.edit_profile_settings(user,
                                      set_trade=profile.EXCHANGE_SETTING_ACCEPTING,
                                      set_request=profile.EXCHANGE_SETTING_NOT_ACCEPTING,
                                      set_commission=profile.EXCHANGE_SETTING_FULL_QUEUE)
        test_user_profile = profile.select_profile(user)
        exchange_settings = _exchange_settings_from_settings_string(test_user_profile['settings'])
        self.assertEqual(exchange_settings[profile.EXCHANGE_TYPE_TRADE], profile.EXCHANGE_SETTING_ACCEPTING)
        self.assertEqual(exchange_settings[profile.EXCHANGE_TYPE_REQUEST], profile.EXCHANGE_SETTING_NOT_ACCEPTING)
        self.assertEqual(exchange_settings[profile.EXCHANGE_TYPE_COMMISSION], profile.EXCHANGE_SETTING_FULL_QUEUE)


@pytest.mark.usefixtures('db', 'drop_email')
def test_edit_email_password(monkeypatch):
    monkeypatch.setattr(profile, 'invalidate_other_sessions', lambda x: '')

    from weasyl.login import verify_email_change

    password = "01234556789"
    username = "test0042"
    email = "test@weasyl.com"
    userid = db_utils.create_user(username=username, password=password, email_addr=email)

    # Case 1: No changes, user authentication succeeds
    assert not profile.edit_email_password(
        userid=userid,
        password=password,
        newemail="",
        newpassword="",
    )

    # Case 2: No changes, user authentication fails
    with pytest.raises(WeasylError) as err:
        profile.edit_email_password(
            userid=userid,
            password="notTheRightPassword",
            newemail="",
            newpassword="",
        )
    assert 'passwordIncorrect' == err.value.value

    # Case 3: Changes, new password only, password too short/'insecure'
    with pytest.raises(WeasylError) as err:
        profile.edit_email_password(
            userid=userid,
            password=password,
            newemail="",
            newpassword="012345",
        )
    assert 'passwordInsecure' == err.value.value

    # Case 5: Changes, new password only, password change succeeds
    result = profile.edit_email_password(
        userid=userid,
        password=password,
        newemail="",
        newpassword="1122334455",
    )
    assert "Your password has been successfully changed" in result
    password = "1122334455"

    # Case 7: Changes, new email only, email already in use
    db_utils.create_user(email_addr="testB@weasyl.com")
    profile.edit_email_password(
        userid=userid,
        password=password,
        newemail="testB@weasyl.com",
        newpassword="",
    )
    query = d.engine.scalar("""
        SELECT email FROM emailverify WHERE userid = %(userid)s LIMIT 1
    """, userid=userid)
    assert not query

    # Case 8: Changes, new email only, email change succeeds
    newemailaddr = "testC@weasyl.com"
    result = profile.edit_email_password(
        userid=userid,
        password=password,
        newemail=newemailaddr,
        newpassword="",
    )
    assert "Your email change request is currently pending" in result
    query = d.engine.execute("""
        SELECT userid, email, token, createtimestamp
        FROM emailverify
        WHERE userid = %(userid)s
    """, userid=userid).fetchone()
    QID, QEMAIL, QTOKEN, QTIMESTAMP = query
    assert QID == userid
    assert QEMAIL == newemailaddr
    assert len(QTOKEN) == 40
    assert arrow.get(QTIMESTAMP)

    # Now that we have the token, let's also verify that ``login.verify_email_change`` works.
    #   It's as good a place as any.
    # Case 8.1/8.2: Make sure invalid token and/or userid doesn't work.
    with pytest.raises(WeasylError) as err:
        verify_email_change(None, "a")
    assert "Unexpected" == err.value.value
    with pytest.raises(WeasylError) as err:
        verify_email_change(1, None)
    assert "Unexpected" == err.value.value

    # Case 8.3: An incorrect token is provided.
    with pytest.raises(WeasylError) as err:
        verify_email_change(userid, "a")
    assert "ChangeEmailVerificationTokenIncorrect" == err.value.value

    # Case 8.4: Correct token is provided, and the new email is written to `login`
    result = verify_email_change(userid, QTOKEN)
    assert result == newemailaddr
    query = d.engine.scalar("""
        SELECT email
        FROM login
        WHERE userid = %(userid)s
    """, userid=userid)
    assert query == QEMAIL

    # Case 9: Email and password changed at the same time.
    newemailaddr = "testD@weasyl.com"
    newpassword = "test123_test123_test123"
    result = profile.edit_email_password(
        userid=userid,
        password=password,
        newemail=newemailaddr,
        newpassword=newpassword,
    )
    assert "Your password has been successfully changed" in result
    assert "Your email change request is currently pending" in result

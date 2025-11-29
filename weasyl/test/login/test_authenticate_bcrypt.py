import datetime
import json

import pytest

from libweasyl import staff
from libweasyl.legacy import get_offset_unixtime
from weasyl import define as d
from weasyl import login
from weasyl import macro
from weasyl.login import InvalidCredentials
from weasyl.test import db_utils


user_name = "test"

# Main test password
raw_password = "0123456789"


@pytest.mark.usefixtures('db')
def test_login_fails_if_no_username_provided():
    result = login.authenticate_bcrypt(username='', password='password', request=None)
    assert result == InvalidCredentials(username_exists=False, inactive_username_exists=False)


@pytest.mark.usefixtures('db')
def test_login_fails_if_no_password_provided():
    result = login.authenticate_bcrypt(username=user_name, password='', request=None)

    # Not a possible case with HTML form validation, so we don’t care what the specific result is
    assert isinstance(result, InvalidCredentials)


@pytest.mark.usefixtures('db')
def test_login_fails_if_incorrect_username_is_provided():
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == InvalidCredentials(username_exists=False, inactive_username_exists=False)


@pytest.mark.usefixtures('db')
def test_login_fails_for_incorrect_credentials():
    random_password = "ThisIsARandomPassword"
    db_utils.create_user(password=random_password, username=user_name)
    another_random_password = "ThisIsNotTheSamePassword"
    result = login.authenticate_bcrypt(username=user_name, password=another_random_password, request=None)
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)


@pytest.mark.usefixtures('db')
def test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account(tmp_path, monkeypatch):
    # Required: Monkeypatch the log directory, and the staff.MODS frozenset
    monkeypatch.setattr(macro, 'MACRO_SYS_LOG_PATH', f"{tmp_path}/")
    log_path = '%s%s.%s.log' % (macro.MACRO_SYS_LOG_PATH, 'login.fail', d.get_timestamp())
    user_id = db_utils.create_user(username='ikani', password=raw_password)
    # Set the moderators in libweasyl/staff.py via monkeypatch
    monkeypatch.setattr(staff, 'MODS', frozenset([user_id]))
    # Ensure we are actually writing to the file by counting the file's lines
    prerun_loglines = 0
    # The file might not exist; this is fine; ignore
    try:
        with open(log_path, 'r') as log:
            for line in log:
                prerun_loglines += 1
            log.close()
    except IOError:
        pass
    postrun_loglines = 0
    # Item under test
    result = login.authenticate_bcrypt(username='ikani', password='FakePassword', request=None)
    # Verify we are writing to the log file as expected
    with open(log_path, 'r') as log:
        for line in log:
            postrun_loglines += 1
        last_line = line
        log.close()
    last_line_dict = json.loads(last_line)
    assert postrun_loglines > prerun_loglines
    assert last_line_dict['userid'] == user_id
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)


@pytest.mark.usefixtures('db')
def test_login_fails_if_user_is_banned():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    db_utils.create_banuser(userid=user_id, reason="Testing")
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == login.Banned(user_id)


@pytest.mark.usefixtures('db')
def test_login_fails_if_user_is_suspended():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    release_date = d.get_time() + 60
    db_utils.create_suspenduser(userid=user_id, reason="Testing", release=release_date)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == login.Suspended(user_id)


@pytest.mark.usefixtures('db')
def test_login_succeeds_if_suspension_duration_has_expired():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    release_date = get_offset_unixtime(datetime.datetime(2015, 12, 31, tzinfo=datetime.timezone.utc))
    db_utils.create_suspenduser(userid=user_id, reason="Testing", release=release_date)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == login.Success(user_id)


@pytest.mark.usefixtures('db')
def test_login_succeeds_for_valid_username_and_password():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == login.Success(user_id)


@pytest.mark.usefixtures('db')
def test_unicode_password():
    user_id = db_utils.create_user(password="passwordé", username=user_name)
    result = login.authenticate_bcrypt(username=user_name, password="passwordé", request=None)
    assert result == login.Success(user_id)
    result = login.authenticate_bcrypt(username=user_name, password="passworde", request=None)
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)
    result = login.authenticate_bcrypt(username=user_name, password="password", request=None)
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)


@pytest.mark.usefixtures('db')
def test_unicode_attempts():
    user_id = db_utils.create_user(password="password", username=user_name)
    result = login.authenticate_bcrypt(username=user_name, password="passwordé", request=None)
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)
    result = login.authenticate_bcrypt(username=user_name, password="passwörd", request=None)
    assert result == InvalidCredentials(username_exists=True, inactive_username_exists=False)
    result = login.authenticate_bcrypt(username=user_name, password="password", request=None)
    assert result == login.Success(user_id)

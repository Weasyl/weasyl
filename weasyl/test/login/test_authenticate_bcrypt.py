# encoding: utf-8
from __future__ import absolute_import

import pytest
import json

from libweasyl import staff
from weasyl import define as d
from weasyl import login
from weasyl import macro
from weasyl.test import db_utils


user_name = "test"

# Main test password
raw_password = "0123456789"


@pytest.mark.usefixtures('db')
def test_login_fails_if_no_username_provided():
    result = login.authenticate_bcrypt(username='', password='password', request=None)
    assert result == (0, 'invalid')


@pytest.mark.usefixtures('db')
def test_login_fails_if_no_password_provided():
    result = login.authenticate_bcrypt(username=user_name, password='', request=None)
    assert result == (0, 'invalid')


@pytest.mark.usefixtures('db')
def test_login_fails_if_incorrect_username_is_provided():
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == (0, 'invalid')


@pytest.mark.usefixtures('db')
def test_login_fails_for_incorrect_credentials():
    random_password = "ThisIsARandomPassword"
    db_utils.create_user(password=random_password, username=user_name)
    another_random_password = "ThisIsNotTheSamePassword"
    result = login.authenticate_bcrypt(username=user_name, password=another_random_password, request=None)
    assert result == (0, 'invalid')


@pytest.mark.usefixtures('db')
def test_login_fails_for_invalid_auth_and_logs_failure_if_mod_account(tmpdir, monkeypatch):
    # Required: Monkeypatch the log directory, and the staff.MODS frozenset
    monkeypatch.setenv(macro.MACRO_SYS_LOG_PATH, tmpdir + "/")
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
    assert result == (0, 'invalid')


@pytest.mark.usefixtures('db')
def test_login_fails_if_user_is_banned():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    d.engine.execute("UPDATE login SET settings = 'b' WHERE userid = %(id)s", id=user_id)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == (user_id, 'banned')


@pytest.mark.usefixtures('db')
def test_login_fails_if_user_is_suspended():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    d.engine.execute("UPDATE login SET settings = 's' WHERE userid = %(id)s", id=user_id)
    release_date = d.get_time() + 60
    d.engine.execute("INSERT INTO suspension VALUES (%(id)s, %(reason)s, %(rel)s)",
                     id=user_id, reason='test', rel=release_date)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == (user_id, 'suspended')


@pytest.mark.usefixtures('db')
def test_login_succeeds_if_suspension_duration_has_expired():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    d.engine.execute("UPDATE login SET settings = 's' WHERE userid = %(id)s", id=user_id)
    release_date = d.convert_unixdate(31, 12, 2015)
    d.engine.execute("INSERT INTO suspension VALUES (%(id)s, %(reason)s, %(rel)s)",
                     id=user_id, reason='test', rel=release_date)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == (user_id, None)


@pytest.mark.usefixtures('db')
def test_logins_with_unicode_failures_succeed_with_corresponding_status():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    # This hash corresponds to "password"
    old_2a_bcrypt_hash = '$2a$04$uOBx2JziJoxjq/F88NjQZ.8mRGE8FgLi3q0Rm3QUlBZnhhInXCb9K'
    d.engine.execute("UPDATE authbcrypt SET hashsum = %(hash)s WHERE userid = %(id)s",
                     hash=old_2a_bcrypt_hash, id=user_id)
    result = login.authenticate_bcrypt(user_name, u"passwordé", request=None)
    assert result == (user_id, 'unicode-failure')


@pytest.mark.usefixtures('db')
def test_login_succeeds_for_valid_username_and_password():
    user_id = db_utils.create_user(password=raw_password, username=user_name)
    result = login.authenticate_bcrypt(username=user_name, password=raw_password, request=None)
    assert result == (user_id, None)

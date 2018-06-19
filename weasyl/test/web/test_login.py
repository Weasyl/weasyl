from __future__ import absolute_import

import pyotp
import pytest

from weasyl import define as d
from weasyl import two_factor_auth as tfa
from weasyl.test import db_utils
from weasyl.test.web.wsgi import app


@pytest.mark.usefixtures('db', 'cache')
def test_user_change_changes_token():
    user = db_utils.create_user(username='user1', password='password1')

    resp = app.get('/')
    cookie = resp.headers['Set-Cookie'].split(';', 1)[0]
    csrf = resp.html.find('html')['data-csrf-token']

    resp = app.get('/', headers={'Cookie': cookie})
    assert resp.html.find('html')['data-csrf-token'] == csrf

    resp = app.post('/signin', {'token': csrf, 'username': 'user1', 'password': 'password1'}, headers={'Cookie': cookie})
    assert 'Set-Cookie' in resp.headers
    new_cookie = resp.headers['Set-Cookie'].split(';', 1)[0]
    resp = resp.follow()
    new_csrf = resp.html.find('html')['data-csrf-token']
    assert new_cookie != cookie
    assert new_csrf != csrf

    sessionid = d.engine.scalar("SELECT sessionid FROM sessions WHERE userid = %(user)s", user=user)
    assert sessionid is not None

    resp = app.get('/signout?token=' + new_csrf[:8], headers={'Cookie': new_cookie})
    assert 'Set-Cookie' in resp.headers
    new_cookie_2 = resp.headers['Set-Cookie'].split(';', 1)[0]
    resp = resp.follow()
    new_csrf_2 = resp.html.find('html')['data-csrf-token']
    assert new_cookie_2 != new_cookie
    assert new_cookie_2 != cookie
    assert new_csrf_2 != new_csrf
    assert new_csrf_2 != csrf

    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE sessionid = %(id)s)", id=sessionid)


@pytest.mark.usefixtures('db', 'cache')
def test_2fa_changes_token():
    user = db_utils.create_user(username='user1', password='password1')

    resp = app.get('/')
    cookie = resp.headers['Set-Cookie'].split(';', 1)[0]
    csrf = resp.html.find('html')['data-csrf-token']

    assert tfa.store_recovery_codes(user, ','.join(tfa.generate_recovery_codes()))
    tfa_secret = pyotp.random_base32()
    totp = pyotp.TOTP(tfa_secret)
    tfa_response = totp.now()
    assert tfa.activate(user, tfa_secret, tfa_response)

    resp = app.post('/signin', {'token': csrf, 'username': 'user1', 'password': 'password1'}, headers={'Cookie': cookie})
    assert 'Set-Cookie' in resp.headers
    new_cookie = resp.headers['Set-Cookie'].split(';', 1)[0]
    new_csrf = resp.html.find('html')['data-csrf-token']
    assert new_cookie != cookie
    assert new_csrf != csrf
    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE userid = %(user)s)", user=user)
    assert d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE additional_data->'2fa_pwd_auth_userid' = %(user)s::text)", user=user)

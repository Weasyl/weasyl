from __future__ import absolute_import

import pyotp
import pytest

from libweasyl import security
from weasyl import define as d
from weasyl import two_factor_auth as tfa
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache')
def test_user_change_changes_token(app):
    user = db_utils.create_user(username='user1', password='password1')

    resp = app.get('/')
    old_cookie = app.cookies['WZL']
    csrf = resp.html.find('html')['data-csrf-token']

    resp = app.get('/')
    assert resp.html.find('html')['data-csrf-token'] == csrf

    resp = app.post('/signin', {'token': csrf, 'username': 'user1', 'password': 'password1'})
    new_cookie = app.cookies['WZL']
    resp = resp.follow()
    new_csrf = resp.html.find('html')['data-csrf-token']
    assert new_cookie != old_cookie
    assert new_csrf != csrf

    sessionid = d.engine.scalar("SELECT sessionid FROM sessions WHERE userid = %(user)s", user=user)
    assert sessionid is not None

    resp = app.get('/signout?token=' + new_csrf[:8])
    new_cookie_2 = app.cookies['WZL']
    resp = resp.follow()
    new_csrf_2 = resp.html.find('html')['data-csrf-token']
    assert new_cookie_2 != new_cookie
    assert new_cookie_2 != old_cookie
    assert new_csrf_2 != new_csrf
    assert new_csrf_2 != csrf

    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE sessionid = %(id)s)", id=sessionid)


@pytest.mark.usefixtures('db', 'cache')
def test_2fa_changes_token(app):
    user = db_utils.create_user(username='user1', password='password1')

    resp = app.get('/')
    csrf = resp.html.find('html')['data-csrf-token']

    assert tfa.store_recovery_codes(user, ','.join(tfa.generate_recovery_codes()))
    tfa_secret = pyotp.random_base32()
    totp = pyotp.TOTP(tfa_secret)
    tfa_response = totp.now()
    assert tfa.activate(user, tfa_secret, tfa_response)

    old_cookie = app.cookies['WZL']
    resp = app.post('/signin', {'token': csrf, 'username': 'user1', 'password': 'password1'})
    new_csrf = resp.html.find('html')['data-csrf-token']
    assert app.cookies['WZL'] != old_cookie
    assert new_csrf != csrf
    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE userid = %(user)s)", user=user)
    assert d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE additional_data->'2fa_pwd_auth_userid' = %(user)s::text)", user=user)


@pytest.mark.usefixtures('db', 'cache')
def test_guest_session_upgrade(app):
    db_utils.create_user(username='user1', password='password1')

    old_cookie = db_utils.create_session(None).split('=')[1]
    old_csrf = security.generate_key(64)
    d.engine.execute("UPDATE sessions SET csrf_token = %(csrf)s WHERE sessionid = %(id)s", id=old_cookie, csrf=old_csrf)

    resp = app.get('/', headers={'Cookie': 'WZL=' + old_cookie})
    csrf = resp.html.find('html')['data-csrf-token']

    assert 'WZL' not in app.cookies
    assert '__Host-WZLcsrf' in app.cookies
    assert csrf == old_csrf

    resp = app.get('/')
    csrf = resp.html.find('html')['data-csrf-token']
    assert app.cookies['WZL'] != old_cookie and len(app.cookies['WZL']) == 20
    assert csrf != old_csrf

    resp = app.post('/signin', {'token': old_csrf.encode('rot13'), 'username': 'user1', 'password': 'password1'}, status=403)
    assert resp.html.find(id='error_content').p.text.startswith(u"This action appears to have been performed illegitimately")

    d.engine.execute("DELETE FROM sessions WHERE sessionid = %(id)s", id=old_cookie)

    # ensure the new CSRF token works
    app.post('/signin', {'token': csrf, 'username': 'user2', 'password': 'password2'})

    # ensure the old CSRF token works
    app.post('/signin', {'token': old_csrf, 'username': 'user1', 'password': 'password1'}).follow()

    # ensure the old CSRF token stops working when signed in
    resp = app.post('/submit/visual', {'token': old_csrf}, status=403)
    assert resp.html.find(id='error_content').p.text.startswith(u"This action appears to have been performed illegitimately")

import pyotp
import pytest

from weasyl import define as d
from weasyl import two_factor_auth as tfa
from weasyl.define import ORIGIN
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache')
def test_user_change_changes_token(app):
    user = db_utils.create_user(username='user1', password='password1')

    app.get('/')
    assert 'WZL' not in app.cookies

    app.post('/signin', {'username': 'user1', 'password': 'password1'})
    new_cookie = app.cookies.get('WZL')
    assert new_cookie

    sessionid = d.engine.scalar("SELECT sessionid FROM sessions WHERE userid = %(user)s", user=user)
    assert sessionid is not None

    resp = app.post('/signout')
    assert 'WZL' not in app.cookies
    resp.follow()

    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE sessionid = %(id)s)", id=sessionid)


@pytest.mark.usefixtures('db', 'cache')
def test_2fa_changes_token(app):
    user = db_utils.create_user(username='user1', password='password1')

    assert tfa.store_recovery_codes(user, ','.join(tfa.generate_recovery_codes()))
    tfa_secret = pyotp.random_base32()
    totp = pyotp.TOTP(tfa_secret)
    tfa_response = totp.now()
    assert tfa.activate(user, tfa_secret, tfa_response)

    assert 'WZL' not in app.cookies
    app.post('/signin', {'username': 'user1', 'password': 'password1'})
    assert app.cookies.get('WZL')
    assert not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE userid = %(user)s)", user=user)
    assert d.engine.scalar("SELECT EXISTS (SELECT 0 FROM sessions WHERE additional_data->'2fa_pwd_auth_userid' = %(user)s::text)", user=user)


@pytest.mark.parametrize('release', [True, False])
@pytest.mark.usefixtures('db', 'cache')
def test_username_change(app, release):
    user = db_utils.create_user(username='user1', password='password1')
    app.set_cookie(*db_utils.create_session(user).split('=', 1))

    resp = app.get('/control/username')

    assert 'username_release' not in resp.forms
    assert 'disabled' not in resp.html.find(id='new_username').attrs
    assert resp.html.find(id='avatar')['alt'] == 'user1'
    assert app.get('/~user1').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user1'
    assert app.get('/~user1snewusername', status=404).html.find(id='error_content').p.string == "This user doesn't seem to be in our database."

    form = resp.forms['username_change']
    form['new_username'] = "user1's new username"
    assert form.submit('do').html.find(id='error_content').p.string == 'Your username has been changed.'

    resp = app.get('/control/username')

    assert 'username_release' in resp.forms
    assert 'disabled' in resp.html.find(id='new_username').attrs
    assert resp.html.find(id='avatar')['alt'] == "user1's new username"
    assert app.get('/~user1').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user1snewusername'
    assert app.get('/~user1snewusername').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user1snewusername'

    if release:
        form = resp.forms['username_release']
        assert form.submit('do').html.find(id='error_content').p.string == 'Your old username has been released.'

        resp = app.get('/control/username')

        assert resp.html.find(id='avatar')['alt'] == "user1's new username"
        assert app.get('/~user1', status=404).html.find(id='error_content').p.string == "This user doesn't seem to be in our database."
        assert app.get('/~user1snewusername').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user1snewusername'

    form = resp.forms['username_change']
    form['new_username'] = 'user2'
    assert form.submit('do', status=422).html.find(id='error_content').p.string == "You can't change your username within 30 days of a previous change."

    d.engine.execute("UPDATE username_history SET replaced_at = replaced_at - INTERVAL '30 days'")
    assert form.submit('do').html.find(id='error_content').p.string == 'Your username has been changed.'

    resp = app.get('/control/username')

    assert resp.html.find(id='avatar')['alt'] == 'user2'
    assert app.get('/~user1', status=404).html.find(id='error_content').p.string == "This user doesn't seem to be in our database."
    assert app.get('/~user1snewusername').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user2'
    assert app.get('/~user2').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user2'

    form = resp.forms['username_change']
    form['new_username'] = 'U S E R 2'
    d.engine.execute("UPDATE username_history SET replaced_at = replaced_at - INTERVAL '30 days'")
    assert form.submit('do').html.find(id='error_content').p.string == 'Your username has been changed.'

    resp = app.get('/control/username')

    assert 'disabled' not in resp.html.find(id='new_username').attrs
    assert resp.html.find(id='avatar')['alt'] == 'U S E R 2'
    assert app.get('/~user1snewusername').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user2'
    assert app.get('/~user2').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user2'

    form = resp.forms['username_change']
    form['new_username'] = 'user3'
    assert form.submit('do').html.find(id='error_content').p.string == 'Your username has been changed.'

    resp = app.get('/control/username')

    assert resp.html.find(id='avatar')['alt'] == 'user3'
    assert app.get('/~user1snewusername', status=404).html.find(id='error_content').p.string == "This user doesn't seem to be in our database."
    assert app.get('/~user2').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user3'
    assert app.get('/~user3').html.select_one('link[rel=canonical]')['href'] == f'{ORIGIN}/~user3'

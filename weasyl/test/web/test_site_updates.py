from __future__ import absolute_import, unicode_literals

import pytest

from libweasyl import staff
from libweasyl.legacy import UNIXTIME_OFFSET
from weasyl import errorcode
from weasyl import siteupdate
from weasyl.define import sessionmaker
from weasyl.test import db_utils
from weasyl.test.web.wsgi import app


_FORM = {
    u'title': u'Title',
    u'content': u'Content',
}


@pytest.fixture(name='site_updates')
@pytest.mark.usefixtures('db')
def _site_updates():
    user = db_utils.create_user(username='test_username')

    updates = [
        siteupdate.create(user, u'foo', u'content one'),
        siteupdate.create(user, u'bar', u'content two'),
        siteupdate.create(user, u'baz', u'content three'),
    ]

    for update in updates:
        sessionmaker().expunge(update)

    return (user, updates)


@pytest.mark.usefixtures('db')
def test_select_last_empty():
    assert siteupdate.select_last() is None


@pytest.mark.usefixtures('db')
def test_select_last(site_updates):
    user, updates = site_updates
    most_recent = updates[-1]

    selected = siteupdate.select_last()
    assert 'display_url' in selected.pop('user_media')['avatar'][0]
    assert selected == {
        'updateid': most_recent.updateid,
        'userid': user,
        'username': 'test_username',
        'title': most_recent.title,
        'content': most_recent.content,
        'unixtime': most_recent.unixtime.timestamp + UNIXTIME_OFFSET,
    }


@pytest.mark.usefixtures('db', 'cache')
def test_index_empty():
    resp = app.get('/')
    assert resp.html.find(id='home-content') is not None
    assert resp.html.find(id='hc-update') is None


@pytest.mark.usefixtures('db', 'cache')
def test_index(site_updates):
    _, updates = site_updates
    resp = app.get('/')
    update = resp.html.find(id='hc-update')
    assert update is not None
    assert update.h3.string == updates[-1].title
    assert update.figure.img['alt'] == u'avatar of test_username'


@pytest.mark.usefixtures('db')
def test_list_empty():
    resp = app.get('/site-updates/')
    assert resp.html.find(None, 'content').p.string == u'No site updates to show.'


@pytest.mark.usefixtures('db')
def test_list(monkeypatch, site_updates):
    _, updates = site_updates
    resp = app.get('/site-updates/')
    assert len(resp.html.findAll(None, 'text-post-item')) == 3
    assert resp.html.find(None, 'text-post-actions') is None
    assert len(resp.html.findAll(None, 'text-post-group-header')) == 1

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))
    resp = app.get('/site-updates/', headers={'Cookie': cookie})
    assert len(resp.html.findAll(None, 'text-post-item')) == 3
    assert resp.html.find(None, 'text-post-actions').a['href'] == '/site-updates/%d/edit' % (updates[-1].updateid,)


@pytest.mark.usefixtures('db', 'no_csrf')
def test_create(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': cookie}).follow()
    assert resp.html.find(None, 'content').h3.string == _FORM['title']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_create_strip(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post(
        '/admincontrol/siteupdate',
        dict(_FORM, title=' test title \t '),
        headers={'Cookie': cookie},
    ).follow()
    assert resp.html.find(None, 'content').h3.string == u'test title'


@pytest.mark.usefixtures('db')
def test_create_csrf(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.token


@pytest.mark.usefixtures('db')
def test_create_restricted(monkeypatch):
    resp = app.get('/admincontrol/siteupdate')
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned
    resp = app.post('/admincontrol/siteupdate', _FORM)
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/admincontrol/siteupdate', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([user]))
    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.get('/admincontrol/siteupdate', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.get('/admincontrol/siteupdate', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content') is None


@pytest.mark.usefixtures('db', 'no_csrf')
def test_create_validation(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/admincontrol/siteupdate', {'title': u'', 'content': u'Content'}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['titleInvalid']

    resp = app.post('/admincontrol/siteupdate', {'title': u'Title', 'content': u''}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['contentInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_create_notifications(monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': admin_cookie}).follow()
    assert resp.html.find(None, 'content').h3.string == _FORM['title']

    normal_cookie = db_utils.create_session(normal_user)
    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Notifications').stripped_strings)[1] == '1'
    assert resp.html.find(id='site_updates').find(None, 'item').a.string == _FORM['title']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_edit(monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), _FORM, headers={'Cookie': cookie}).follow()
    assert resp.html.find(None, 'content').h3.string == _FORM['title']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_edit_strip(monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post(
        '/site-updates/%d' % (updates[-1].updateid,),
        dict(_FORM, title=' test title \t '),
        headers={'Cookie': cookie},
    ).follow()
    assert resp.html.find(None, 'content').h3.string == u'test title'


@pytest.mark.usefixtures('db', 'no_csrf')
def test_edit_nonexistent(monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    app.post('/site-updates/%d' % (updates[-1].updateid + 1,), _FORM, headers={'Cookie': cookie}, status=404)


@pytest.mark.usefixtures('db')
def test_edit_csrf(monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.token


@pytest.mark.usefixtures('db')
def test_edit_restricted(monkeypatch, site_updates):
    _, updates = site_updates

    resp = app.get('/site-updates/%d/edit' % (updates[-1].updateid,))
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned
    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), _FORM)
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/site-updates/%d/edit' % (updates[-1].updateid,), headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([user]))
    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.get('/site-updates/%d/edit' % (updates[-1].updateid,), headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), _FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.get('/site-updates/%d/edit' % (updates[-1].updateid,), headers={'Cookie': cookie})
    assert resp.html.find(id='error_content') is None


@pytest.mark.usefixtures('db', 'no_csrf')
def test_edit_validation(monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), {'title': u'', 'content': u'Content'}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['titleInvalid']

    resp = app.post('/site-updates/%d' % (updates[-1].updateid,), {'title': u'Title', 'content': u''}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['contentInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_edit_notifications(monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    resp = app.post('/admincontrol/siteupdate', _FORM, headers={'Cookie': admin_cookie}).follow()
    assert resp.html.find(None, 'content').h3.string == _FORM['title']

    normal_cookie = db_utils.create_session(normal_user)
    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Notifications').stripped_strings)[1] == '1'
    assert resp.html.find(id='site_updates').find(None, 'item').a.string == _FORM['title']

    resp = app.post(
        '/site-updates/%d' % (siteupdate.select_last()['updateid'],),
        dict(_FORM, title=u'New title'),
        headers={'Cookie': admin_cookie},
    ).follow()
    assert resp.html.find(None, 'content').h3.string == u'New title'

    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Notifications').stripped_strings)[1] == '1'
    assert resp.html.find(id='site_updates').find(None, 'item').a.string == u'New title'

import pytest

from libweasyl import staff
from weasyl import define
from weasyl import errorcode
from weasyl import siteupdate
from weasyl.test import db_utils


_FORM = {
    'title': 'Title',
    'content': 'Content',
}


@pytest.fixture(name='site_updates')
def _site_updates(db, cache):
    user = db_utils.create_user(username='test_username')

    updates = [
        {'userid': user, 'title': 'foo', 'content': 'content one', 'wesley': False},
        {'userid': user, 'title': 'bar', 'content': 'content two', 'wesley': False},
        {'userid': user, 'title': 'baz', 'content': 'content three', 'wesley': False},
    ]

    for update in updates:
        update['updateid'] = siteupdate.create(**update)

    return (user, updates)


@pytest.mark.usefixtures('db')
def test_select_last_empty(app):
    assert siteupdate.select_last() is None


@pytest.mark.usefixtures('db')
def test_select_last(app, site_updates):
    user, updates = site_updates
    most_recent = updates[-1]

    selected = siteupdate.select_last()
    assert 'display_url' in selected.pop('user_media')['avatar'][0]
    assert isinstance(selected.pop('unixtime'), int)
    assert selected == {
        'updateid': most_recent['updateid'],
        'userid': user,
        'username': 'test_username',
        'title': most_recent['title'],
        'content': most_recent['content'],
        'comment_count': 0,
    }


@pytest.mark.usefixtures('db', 'cache')
def test_index_empty(app):
    resp = app.get('/')
    assert resp.html.find(id='hc-streams') is not None
    assert resp.html.find(id='hc-update') is None


@pytest.mark.usefixtures('db', 'cache')
def test_index(app, site_updates):
    _, updates = site_updates
    resp = app.get('/')
    update = resp.html.find(id='hc-update')
    assert update is not None
    assert update.h3.string == updates[-1]['title']
    assert list(update.select_one('.hc-update-attribution > .username').stripped_strings) == ['test_username']


@pytest.mark.usefixtures('db')
def test_list_empty(app):
    resp = app.get('/site-updates/')
    assert resp.html.find(None, 'text-post-list').p.string == 'No site updates to show.'


@pytest.mark.usefixtures('db')
def test_list(app, monkeypatch, site_updates):
    _, updates = site_updates
    resp = app.get('/site-updates/')
    assert len(resp.html.findAll(None, 'text-post-item')) == 3
    assert resp.html.find(None, 'text-post-edit') is None

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))
    resp = app.get('/site-updates/', headers={'Cookie': cookie})
    assert len(resp.html.findAll(None, 'text-post-item')) == 3
    assert resp.html.find(None, 'text-post-actions').a['href'] == '/site-updates/%d/edit' % (updates[-1]['updateid'],)


@pytest.mark.usefixtures('db')
def test_create(app, monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/', _FORM, headers={'Cookie': cookie}).follow()
    assert resp.html.find(id='home-content').h3.string == _FORM['title']


@pytest.mark.usefixtures('db')
def test_create_strip(app, monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post(
        '/site-updates/',
        dict(_FORM, title=' test title \t '),
        headers={'Cookie': cookie},
    ).follow()
    assert resp.html.find(id='home-content').h3.string == 'test title'


@pytest.mark.usefixtures('db')
def test_create_restricted(app, monkeypatch):
    resp = app.get('/site-updates/new', status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.unsigned
    resp = app.post('/site-updates/', _FORM, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/site-updates/new', headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission
    resp = app.post('/site-updates/', _FORM, headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission

    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.get('/site-updates/new', headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission
    resp = app.post('/site-updates/', _FORM, headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission

    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.get('/site-updates/new', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content') is None


@pytest.mark.usefixtures('db')
def test_create_validation(app, monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/', {'title': '', 'content': 'Content'}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['titleInvalid']

    resp = app.post('/site-updates/', {'title': 'Title', 'content': ''}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['contentInvalid']


@pytest.mark.usefixtures('db', 'cache')
def test_create_notifications(app, monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    resp = app.post('/site-updates/', _FORM, headers={'Cookie': admin_cookie}).follow()
    assert resp.html.find(id='home-content').h3.string == _FORM['title']

    normal_cookie = db_utils.create_session(normal_user)
    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Site Updates').stripped_strings)[1] == '1'


@pytest.mark.usefixtures('db', 'cache')
def test_read_counter(app, monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    normal_cookie = db_utils.create_session(normal_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    for _ in range(3):
        app.post('/site-updates/', _FORM, headers={'Cookie': admin_cookie})

    updateids = define.get_updateids()

    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    link = resp.html.find(id='header-messages').find(title='Site Updates')
    assert list(link.stripped_strings)[1] == '3'
    assert link['href'] == '/site-updates/'

    resp = app.get(f'/site-updates/{updateids[1]}', headers={'Cookie': normal_cookie})
    link = resp.html.find(id='header-messages').find(title='Site Updates')
    assert list(link.stripped_strings)[1] == '1'
    assert link['href'] == f'/site-updates/{updateids[0]}'

    resp = app.get(f'/site-updates/{updateids[2]}', headers={'Cookie': normal_cookie})
    link = resp.html.find(id='header-messages').find(title='Site Updates')
    assert list(link.stripped_strings)[1] == '1'
    assert link['href'] == f'/site-updates/{updateids[0]}'

    resp = app.get(f'/site-updates/{updateids[0]}', headers={'Cookie': normal_cookie})
    assert not resp.html.find(id='header-messages').find(title='Site Updates')


@pytest.mark.usefixtures('db')
def test_read_markers(app, monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    normal_cookie = db_utils.create_session(normal_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    updateids = []
    for _ in range(3):
        resp = app.post('/site-updates/', _FORM, headers={'Cookie': admin_cookie})
        updateid = int(resp.headers['Location'].rpartition('/')[2])
        updateids.append(updateid)

    resp = app.get('/site-updates/', headers={'Cookie': normal_cookie})
    assert len(resp.html.find_all(class_='text-post-new')) == 3

    resp = app.get('/site-updates/', headers={'Cookie': normal_cookie})
    assert len(resp.html.find_all(class_='text-post-new')) == 0


@pytest.mark.usefixtures('db')
def test_edit(app, monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), _FORM, headers={'Cookie': cookie}).follow()
    assert resp.html.find(id='home-content').h3.string == _FORM['title']


@pytest.mark.usefixtures('db')
def test_edit_strip(app, monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post(
        '/site-updates/%d' % (updates[-1]['updateid'],),
        dict(_FORM, title=' test title \t '),
        headers={'Cookie': cookie},
    ).follow()
    assert resp.html.find(id='home-content').h3.string == 'test title'


@pytest.mark.usefixtures('db')
def test_edit_nonexistent(app, monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    app.post('/site-updates/%d' % (updates[-1]['updateid'] + 1,), _FORM, headers={'Cookie': cookie}, status=404)


@pytest.mark.usefixtures('db')
def test_edit_restricted(app, monkeypatch, site_updates):
    _, updates = site_updates

    resp = app.get('/site-updates/%d/edit' % (updates[-1]['updateid'],), status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.unsigned
    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), _FORM, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/site-updates/%d/edit' % (updates[-1]['updateid'],), headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission
    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), _FORM, headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission

    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.get('/site-updates/%d/edit' % (updates[-1]['updateid'],), headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission
    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), _FORM, headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.permission

    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.get('/site-updates/%d/edit' % (updates[-1]['updateid'],), headers={'Cookie': cookie})
    assert resp.html.find(id='error_content') is None


@pytest.mark.usefixtures('db')
def test_edit_validation(app, monkeypatch, site_updates):
    _, updates = site_updates

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))

    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), {'title': '', 'content': 'Content'}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['titleInvalid']

    resp = app.post('/site-updates/%d' % (updates[-1]['updateid'],), {'title': 'Title', 'content': ''}, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['contentInvalid']


@pytest.mark.usefixtures('db')
def test_edit_notifications(app, monkeypatch):
    admin_user = db_utils.create_user()
    normal_user = db_utils.create_user()
    admin_cookie = db_utils.create_session(admin_user)
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user]))

    resp = app.post('/site-updates/', _FORM, headers={'Cookie': admin_cookie}).follow()
    assert resp.html.find(id='home-content').h3.string == _FORM['title']

    normal_cookie = db_utils.create_session(normal_user)
    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Site Updates').stripped_strings)[1] == '1'

    resp = app.post(
        '/site-updates/%d' % (siteupdate.select_last()['updateid'],),
        dict(_FORM, title='New title'),
        headers={'Cookie': admin_cookie},
    ).follow()
    assert resp.html.find(id='home-content').h3.string == 'New title'

    resp = app.get('/messages/notifications', headers={'Cookie': normal_cookie})
    assert list(resp.html.find(id='header-messages').find(title='Site Updates').stripped_strings)[1] == '1'

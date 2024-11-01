import pytest

from weasyl import errorcode
from weasyl.test import db_utils


INVALID_PATHS = (
    '/note',
    '/note?',
    '/note?noteid',
    '/note?noteid=',
    '/note?noteid=a',
    '/note?noteid=-1',
    '/note?noteid=9999999999999999999999',
    '/note?noteid=\0',
)


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize('path', INVALID_PATHS)
def test_get_note_guest_invalid(app, path):
    resp = app.get(path, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.unsigned


@pytest.mark.usefixtures('db')
@pytest.mark.parametrize('path', INVALID_PATHS)
def test_get_note_invalid(app, path):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    resp = app.get(path, headers={'Cookie': cookie}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['noteidInvalid']


@pytest.mark.usefixtures('db')
def test_get_note_permissions(app):
    user1 = db_utils.create_user(username='user1')
    cookie1 = db_utils.create_session(user1)
    user2 = db_utils.create_user(username='user2')
    cookie2 = db_utils.create_session(user2)
    user3 = db_utils.create_user(username='user3')
    cookie3 = db_utils.create_session(user3)

    app.post('/notes/compose', {
        'recipient': 'user2',
        'title': 'Title 1',
        'content': 'Content 1',
    }, headers={'Cookie': cookie1})

    app.post('/notes/compose', {
        'recipient': 'user3',
        'title': 'Title 2',
        'content': 'Content 2',
    }, headers={'Cookie': cookie2})

    resp = app.get('/note?noteid=1', headers={'Cookie': cookie1})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 1'

    resp = app.get('/note?noteid=1', headers={'Cookie': cookie2})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 1'

    resp = app.get('/note?noteid=1', headers={'Cookie': cookie3}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['InsufficientPermissions']

    resp = app.get('/note?noteid=2', headers={'Cookie': cookie1}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['InsufficientPermissions']

    resp = app.get('/note?noteid=2', headers={'Cookie': cookie2})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 2'

    resp = app.get('/note?noteid=2', headers={'Cookie': cookie3})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 2'

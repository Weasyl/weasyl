import pytest

from weasyl import errorcode
from weasyl.test import db_utils


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
    resp = app.get('/notes?folder=outbox', headers={'Cookie': cookie1})
    note1_path = resp.html.find('a', string='Title 1')['href']

    app.post('/notes/compose', {
        'recipient': 'user3',
        'title': 'Title 2',
        'content': 'Content 2',
    }, headers={'Cookie': cookie2})
    resp = app.get('/notes?folder=outbox', headers={'Cookie': cookie2})
    note2_path = resp.html.find('a', string='Title 2')['href']

    resp = app.get(note1_path, headers={'Cookie': cookie1})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 1'

    resp = app.get(note1_path, headers={'Cookie': cookie2})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 1'

    resp = app.get(note1_path, headers={'Cookie': cookie3}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['InsufficientPermissions']

    resp = app.get(note2_path, headers={'Cookie': cookie1}, status=403)
    assert resp.html.find(id='error_content').p.text.strip() == errorcode.error_messages['InsufficientPermissions']

    resp = app.get(note2_path, headers={'Cookie': cookie2})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 2'

    resp = app.get(note2_path, headers={'Cookie': cookie3})
    assert resp.html.find(id='note-content').div.div.p.string == 'Content 2'

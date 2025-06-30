import pytest

from weasyl import define as d
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache')
def test_reply_to_restricted_notes(app):
    user1 = db_utils.create_user(username='user1')
    user2 = db_utils.create_user(username='user2')
    session1 = db_utils.create_session(user1)
    session2 = db_utils.create_session(user2)

    d.engine.execute("UPDATE profile SET config = config || 'z' WHERE userid = %(user)s", user=user1)

    def try_send(status):
        app.post('/notes/compose', {
            'recipient': 'user1',
            'title': 'Title',
            'content': 'Content',
        }, headers={'Cookie': session2}, status=status)

    try_send(422)

    app.post('/notes/compose', {
        'recipient': 'user2',
        'title': 'Title',
        'content': 'Content',
    }, headers={'Cookie': session1}, status=303)

    try_send(303)


@pytest.mark.usefixtures('db', 'cache')
def test_reply_when_blocked(app):
    user1 = db_utils.create_user(username='user1')
    user2 = db_utils.create_user(username='user2')
    session1 = db_utils.create_session(user1)
    session2 = db_utils.create_session(user2)

    app.post('/notes/compose', {
        'recipient': 'user2',
        'title': 'Title',
        'content': 'Content',
    }, headers={'Cookie': session1}, status=303)

    app.post('/ignoreuser', {
        'userid': str(user2),
        'action': 'ignore',
    }, headers={'Cookie': session1}, status=303)

    def try_send(status):
        app.post('/notes/compose', {
            'recipient': 'user1',
            'title': 'Title',
            'content': 'Content',
        }, headers={'Cookie': session2}, status=status)

    try_send(422)

    d.engine.execute("UPDATE profile SET config = config || 'z' WHERE userid = %(user)s", user=user1)

    try_send(422)


@pytest.mark.usefixtures('db', 'cache')
def test_preserve_filter_on_page_change(app):
    from1_user = db_utils.create_user(username='from1')
    from2_user = db_utils.create_user(username='from2')
    to_user = db_utils.create_user(username='to')

    from1_session = db_utils.create_session(from1_user)
    from2_session = db_utils.create_session(from2_user)
    to_session = db_utils.create_session(to_user)

    # 50 notes per page, so make 75 to fill a full page and a partial page
    for _ in range(75):
        app.post('/notes/compose', {
            'recipient': 'to',
            'title': 'Title',
            'content': 'Content',
        }, headers={'Cookie': from1_session}, status=303)

    app.post('/notes/compose', {
        'recipient': 'to',
        'title': 'Title',
        'content': 'Content',
    }, headers={'Cookie': from2_session}, status=303)

    resp = app.get('/notes?filter=from1', headers={'Cookie': to_session})
    next_href = resp.html.find('a', rel='next')['href']

    resp = app.get(next_href, headers={'Cookie': to_session})
    assert not resp.html.find_all('a', string='from2')

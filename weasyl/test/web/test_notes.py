from __future__ import absolute_import

import pytest

from weasyl import define as d
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache', 'no_csrf')
def test_reply_to_restricted_notes(app):
    user1 = db_utils.create_user(username='user1')
    user2 = db_utils.create_user(username='user2')
    session1 = db_utils.create_session(user1)
    session2 = db_utils.create_session(user2)

    d.engine.execute("UPDATE profile SET config = config || 'z' WHERE userid = %(user)s", user=user1)

    def _try_send(status):
        app.post('/notes/compose', {
            'recipient': 'user1',
            'title': 'Title',
            'content': 'Content',
        }, headers={'Cookie': session2}, status=status)

    _try_send(422)

    app.post('/notes/compose', {
        'recipient': 'user2',
        'title': 'Title',
        'content': 'Content',
    }, headers={'Cookie': session1}, status=303)

    _try_send(303)


@pytest.mark.usefixtures('db', 'cache', 'no_csrf')
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

    def _try_send(status):
        app.post('/notes/compose', {
            'recipient': 'user1',
            'title': 'Title',
            'content': 'Content',
        }, headers={'Cookie': session2}, status=status)

    _try_send(422)

    d.engine.execute("UPDATE profile SET config = config || 'z' WHERE userid = %(user)s", user=user1)

    _try_send(422)

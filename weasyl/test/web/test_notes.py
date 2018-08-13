from __future__ import absolute_import, unicode_literals

import re

import pytest

from weasyl import define as d
from weasyl import note
from weasyl.test import db_utils
from weasyl.test.utils import Bag


class TestNoteRoute(object):
    @pytest.mark.usefixtures('db')
    def test_bare_note_route_does_not_error(self, app):
        # Ensure visiting ``/note`` alone doesn't raise an unhandled error
        user = db_utils.create_user(username='test1')
        cookie = db_utils.create_session(user)
        resp = app.get('/note', headers={'Cookie': cookie})

        # HTTP303 == HTTPSeeOther
        assert resp.status_int == 303
        resp = resp.follow(headers={'Cookie': cookie})
        resp.mustcontain("There are no private messages to display.")

    @pytest.mark.usefixtures('db')
    def test_visiting_non_numeric_note_route_does_not_error(self, app):
        # Both of these locations aren't valid notes; they shouldn't generate an error.
        test_locations = ['/note?noteid=foo', '/note?noteid=']

        user = db_utils.create_user(username='test1')
        cookie = db_utils.create_session(user)

        for test_location in test_locations:
            resp = app.get(test_location, headers={'Cookie': cookie})

            # HTTP303 == HTTPSeeOther
            assert resp.status_int == 303
            resp = resp.follow(headers={'Cookie': cookie})
            resp.mustcontain("There are no private messages to display.")

    @pytest.mark.usefixtures('db')
    def test_visiting_valid_note_does_not_error(self, app):
        # Ensure visiting ``/note?noteid=NN`` where NN is a valid ID does not error.
        user1 = db_utils.create_user(username='test1usernotes')
        user2 = db_utils.create_user(username='test2usernotes')
        user2_cookie = db_utils.create_session(user2)

        note_form = Bag(
            title="test_note_title_xyz",
            content="test_message_xyz",
            recipient="test2usernotes",
            mod_copy='',
            staff_note='',
        )

        note.send(user1, note_form)

        # Get user2's notes
        resp = app.get('/notes', headers={'Cookie': user2_cookie})

        # Verify we can see the note we just sent manually
        resp.mustcontain("test_note_title_xyz")
        html = resp.html.find_all("a", "unread")

        # Get the note ID out of the HTML
        regex = re.compile("(?:.*noteid=)(\d+)")
        note_id = re.search(regex, str(html)).group(1)

        resp = app.get('/note?noteid=' + note_id, headers={'Cookie': user2_cookie})
        # Verify we have the information we submitted inside the note we retrieved.
        resp.mustcontain("test1usernotes")
        resp.mustcontain("test2usernotes")
        resp.mustcontain("test_note_title_xyz")
        html = resp.html.find_all("div", "formatted-content")
        assert "test_message_xyz" in str(html)


class TestNotesComposeRoute(object):
    @pytest.mark.usefixtures('db', 'cache', 'no_csrf')
    def test_reply_to_restricted_notes(self, app):
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

    @pytest.mark.usefixtures('db', 'cache', 'no_csrf')
    def test_reply_when_blocked(self, app):
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

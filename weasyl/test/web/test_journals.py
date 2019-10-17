

import arrow
import pytest

from libweasyl import ratings
from libweasyl.models.helpers import CharSettings
from weasyl.test import db_utils


@pytest.fixture(name='journal_user')
@pytest.mark.usefixtures('db')
def _journal_user():
    return db_utils.create_user(username='journal_test')


@pytest.fixture(name='journals')
@pytest.mark.usefixtures('db', 'journal_user')
def _journals(journal_user):
    db_utils.create_journal(journal_user, title='Test journal', unixtime=arrow.get(1), content='A test journal')
    db_utils.create_journal(journal_user, title='Public journal', unixtime=arrow.get(2), content='A public journal')
    db_utils.create_journal(journal_user, title='Hidden journal', unixtime=arrow.get(3), content='A hidden journal', settings=CharSettings({'hidden'}, {}, {}))
    db_utils.create_journal(journal_user, title='Restricted journal', rating=ratings.MATURE.code, unixtime=arrow.get(4), content='A journal with a non-General rating')
    db_utils.create_journal(journal_user, title='Recent journal', unixtime=arrow.get(5), content='The most recent journal', settings=CharSettings({'friends-only'}, {}, {}))


@pytest.mark.usefixtures('db', 'journal_user')
def test_profile_empty(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal') is None


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_guest(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == 'Public journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_user(app):
    user = db_utils.create_user(config=CharSettings(frozenset(), {}, {'tagging-level': 'max-rating-mature'}))
    cookie = db_utils.create_session(user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == 'Restricted journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_friend(app, journal_user):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    db_utils.create_friendship(user, journal_user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == 'Recent journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_list_guest(app):
    resp = app.get('/journals/journal_test')
    titles = [link.string for link in resp.html.find(id='journals-content').find_all('a')]
    assert titles == ['Public journal', 'Test journal']


@pytest.mark.usefixtures('db', 'journal_user', 'no_csrf')
def test_create(app, journal_user):
    cookie = db_utils.create_session(journal_user)

    app.post('/submit/journal', {'title': 'Created journal', 'rating': '10', 'content': 'A journal'}, headers={'Cookie': cookie})

    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == 'Created journal'


@pytest.mark.usefixtures('db', 'journal_user')
def test_csrf_on_journal_edit(app, journal_user):
    # Test purpose: Verify that a CSRF token is required to submit a journal entry.
    cookie = db_utils.create_session(journal_user)
    journalid = db_utils.create_journal(journal_user, "Test", content="Test")

    resp = app.post(
        '/edit/journal',
        {'title': 'Created journal', 'rating': '10', 'content': 'A journal', 'journalid': journalid},
        headers={'Cookie': cookie},
        status=403,
    )
    assert resp.html.find(id='error_content').p.text.startswith("This action appears to have been performed illegitimately")


@pytest.mark.usefixtures('db', 'journal_user')
def test_login_required_to_edit_journal(app, journal_user):
    # Test purpose: Verify that an active session is required to even attempt to edit a journal.
    journalid = db_utils.create_journal(journal_user, "Test", content="Test")

    resp = app.post(
        '/edit/journal',
        {'title': 'Created journal', 'rating': '10', 'content': 'A journal', 'journalid': journalid},
    )
    assert "You must be signed in to perform this operation." in resp.html.find(id='error_content').text

import arrow
import pytest

from libweasyl import ratings
from weasyl.test import db_utils


@pytest.fixture(name='journal_user')
def _journal_user(db, cache):
    return db_utils.create_user(username='journal_test')


@pytest.fixture(name='journals')
def _journals(db, journal_user):
    db_utils.create_journal(journal_user, title='Test journal', unixtime=arrow.get(1), content='A test journal')
    db_utils.create_journal(journal_user, title='Public journal', unixtime=arrow.get(2), content='A public journal')
    db_utils.create_journal(journal_user, title='Hidden journal', unixtime=arrow.get(3), content='A hidden journal', hidden=True)
    db_utils.create_journal(journal_user, title='Restricted journal', rating=ratings.MATURE.code, unixtime=arrow.get(4), content='A journal with a non-General rating')
    db_utils.create_journal(journal_user, title='Recent journal', unixtime=arrow.get(5), content='The most recent journal', friends_only=True)


@pytest.mark.usefixtures('db', 'journal_user')
def test_profile_empty(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal') is None


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_guest(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == 'Public journal'


@pytest.mark.usefixtures('db', 'cache', 'journal_user', 'journals')
def test_profile_user(app):
    user = db_utils.create_user(max_rating=ratings.MATURE)
    cookie = db_utils.create_session(user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == 'Restricted journal'


@pytest.mark.usefixtures('db', 'cache', 'journal_user', 'journals')
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


def create_journal(app, user, *, rating):
    resp = app.post("/submit/journal", {"title": "Created journal", "rating": rating, "content": "A journal"})
    assert resp.status_int == 303
    return resp


@pytest.mark.usefixtures('db', 'journal_user')
def test_create(app, journal_user):
    app.set_cookie(*db_utils.create_session(journal_user).split("=", 1))

    create_journal(app, journal_user, rating="10")

    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == 'Created journal'


@pytest.mark.usefixtures('db', 'journal_user')
def test_login_required_to_edit_journal(app, journal_user):
    # Test purpose: Verify that an active session is required to even attempt to edit a journal.
    journalid = db_utils.create_journal(journal_user, "Test", content="Test")

    resp = app.post(
        '/edit/journal',
        {'title': 'Created journal', 'rating': '10', 'content': 'A journal', 'journalid': journalid},
        status=403,
    )
    assert "You must be signed in to perform this operation." in resp.html.find(id='error_content').text

# encoding: utf-8

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
    db_utils.create_journal(journal_user, title=u'Test journal', unixtime=arrow.get(1), content=u'A test journal')
    db_utils.create_journal(journal_user, title=u'Public journal', unixtime=arrow.get(2), content=u'A public journal')
    db_utils.create_journal(journal_user, title=u'Hidden journal', unixtime=arrow.get(3), content=u'A hidden journal', settings=CharSettings({'hidden'}, {}, {}))
    db_utils.create_journal(journal_user, title=u'Restricted journal', rating=ratings.MATURE.code, unixtime=arrow.get(4), content=u'A journal with a non-General rating')
    db_utils.create_journal(journal_user, title=u'Recent journal', unixtime=arrow.get(5), content=u'The most recent journal', settings=CharSettings({'friends-only'}, {}, {}))


@pytest.mark.usefixtures('db', 'journal_user')
def test_profile_empty(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal') is None


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_guest(app):
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == u'Public journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_user(app):
    user = db_utils.create_user(config=CharSettings(frozenset(), {}, {'tagging-level': 'max-rating-mature'}))
    cookie = db_utils.create_session(user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == u'Restricted journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_friend(app, journal_user):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    db_utils.create_friendship(user, journal_user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == u'Recent journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_list_guest(app):
    resp = app.get('/journals/journal_test')
    titles = [link.string for link in resp.html.find(id='journals-content').find_all('a')]
    assert titles == [u'Public journal', u'Test journal']


@pytest.mark.usefixtures('db')
def test_list_unicode_username(app):
    """
    Test journal lists on profiles with usernames containing non-ASCII
    characters, which aren’t supposed to exist but do because of
    a historical bug.
    """
    journal_user = db_utils.create_user(username=u'journál_test')
    db_utils.create_journal(journal_user, title=u'Unícode journal 😊', content=u'A journal and poster username with non-ASCII characters 😊')

    resp = app.get('/journals/journaltest')
    titles = [link.string for link in resp.html.find(id='journals-content').find_all('a')]
    assert titles == [u'Unícode journal 😊']


@pytest.mark.usefixtures('db', 'journal_user', 'no_csrf')
def test_create(app, journal_user):
    cookie = db_utils.create_session(journal_user)

    app.post('/submit/journal', {'title': u'Created journal', 'rating': '10', 'content': u'A journal'}, headers={'Cookie': cookie})

    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == u'Created journal'


@pytest.mark.usefixtures('db', 'journal_user')
def test_csrf_on_journal_edit(app, journal_user):
    # Test purpose: Verify that a CSRF token is required to submit a journal entry.
    cookie = db_utils.create_session(journal_user)
    journalid = db_utils.create_journal(journal_user, "Test", content="Test")

    resp = app.post(
        '/edit/journal',
        {'title': u'Created journal', 'rating': '10', 'content': u'A journal', 'journalid': journalid},
        headers={'Cookie': cookie},
        status=403,
    )
    assert resp.html.find(id='error_content').p.text.startswith(u"This action appears to have been performed illegitimately")


@pytest.mark.usefixtures('db', 'journal_user')
def test_login_required_to_edit_journal(app, journal_user):
    # Test purpose: Verify that an active session is required to even attempt to edit a journal.
    journalid = db_utils.create_journal(journal_user, "Test", content="Test")

    resp = app.post(
        '/edit/journal',
        {'title': u'Created journal', 'rating': '10', 'content': u'A journal', 'journalid': journalid},
        status=403,
    )
    assert "You must be signed in to perform this operation." in resp.html.find(id='error_content').text

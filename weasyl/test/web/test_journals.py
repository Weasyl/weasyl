from __future__ import absolute_import

import arrow
import pytest

from libweasyl import ratings
from libweasyl.models.helpers import CharSettings
from weasyl.test import db_utils
from weasyl.test.web.wsgi import app


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
def test_profile_empty():
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal') is None


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_guest():
    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == u'Public journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_user():
    user = db_utils.create_user(config=CharSettings(frozenset(), {}, {'tagging-level': 'max-rating-mature'}))
    cookie = db_utils.create_session(user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == u'Restricted journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_profile_friend(journal_user):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    db_utils.create_friendship(user, journal_user)

    resp = app.get('/~journal_test', headers={'Cookie': cookie})
    assert resp.html.find(id='user-journal').h4.string == u'Recent journal'


@pytest.mark.usefixtures('db', 'journal_user', 'journals')
def test_list_guest():
    resp = app.get('/journals/journal_test')
    titles = [link.string for link in resp.html.find(id='journals-content').find_all('a')]
    assert titles == [u'Public journal', u'Test journal']


@pytest.mark.usefixtures('db', 'journal_user', 'no_csrf')
def test_create(journal_user):
    cookie = db_utils.create_session(journal_user)

    app.post('/submit/journal', {'title': u'Created journal', 'rating': '10', 'content': u'A journal'}, headers={'Cookie': cookie})

    resp = app.get('/~journal_test')
    assert resp.html.find(id='user-journal').h4.string == u'Created journal'

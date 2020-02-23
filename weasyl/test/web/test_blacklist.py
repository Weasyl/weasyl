# encoding: utf-8
from __future__ import absolute_import

import pytest

from libweasyl import ratings
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache', 'no_csrf')
def test_blacklist_homepage(app):
    """
    Assert that changes to the blacklist apply to the home page immediately.
    """
    submitting_user = db_utils.create_user()
    viewing_user = db_utils.create_user()
    tag1 = db_utils.create_tag('walrus')
    tag2 = db_utils.create_tag('penguin')

    s1 = db_utils.create_submission(submitting_user, rating=ratings.GENERAL.code, subtype=1010)
    db_utils.create_submission_tag(tag1, s1)

    s2 = db_utils.create_submission(submitting_user, rating=ratings.GENERAL.code, subtype=1010)
    db_utils.create_submission_tag(tag2, s2)

    cookie = db_utils.create_session(viewing_user)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 2

    app.post('/manage/tagfilters',
             {'title': 'walrus', 'rating': str(ratings.GENERAL.code), 'do': 'create'},
             headers={'Cookie': cookie}, status=303)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 1

    app.post('/manage/tagfilters',
             {'title': 'walrus', 'rating': str(ratings.GENERAL.code), 'do': 'remove'},
             headers={'Cookie': cookie}, status=303)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 2


@pytest.mark.usefixtures('db', 'cache', 'no_csrf')
def test_block_user_homepage(app):
    """
    Assert that changes to blocked users apply to the home page immediately.
    """
    submitting_user1 = db_utils.create_user()
    submitting_user2 = db_utils.create_user()
    viewing_user = db_utils.create_user()

    db_utils.create_submission(submitting_user1, rating=ratings.GENERAL.code, subtype=1010)
    db_utils.create_submission(submitting_user2, rating=ratings.GENERAL.code, subtype=1010)

    cookie = db_utils.create_session(viewing_user)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 2

    app.post('/ignoreuser',
             {'userid': str(submitting_user1), 'action': 'ignore'},
             headers={'Cookie': cookie}, status=303)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 1

    app.post('/ignoreuser',
             {'userid': str(submitting_user1), 'action': 'unignore'},
             headers={'Cookie': cookie}, status=303)

    resp = app.get('/', headers={'Cookie': cookie})
    resp = resp.html.find('div', {'id': 'home-art'}).find('ul')
    assert len(resp.select('.thumb')) == 2

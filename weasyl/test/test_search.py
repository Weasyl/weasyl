from __future__ import absolute_import

import mock
import pytest

from libweasyl.models.helpers import CharSettings
from libweasyl import ratings
from weasyl.test import db_utils
from weasyl import search


def test_query_parsing():
    assert not search.Query.parse('', 'submit')
    assert not search.Query.parse('#character', 'submit')
    assert search.Query.parse('tag_that_does_not_exist', 'submit')

    query = search.Query.parse('one, two +three & -four |five |six user:a +user:b -user:c #general #mature #submission', 'journal')

    assert query.possible_includes == {'five', 'six'}
    assert query.required_includes == {'one', 'two', 'three'}
    assert query.required_excludes == {'four'}
    assert query.required_user_includes == {'a', 'b'}
    assert query.required_user_excludes == {'c'}
    assert query.ratings == {ratings.GENERAL.code, ratings.MATURE.code}
    assert query.find == 'submit'


@pytest.mark.parametrize(['term', 'n_results'], [
    (u'nothing', 0),
    (u'more nothing', 0),
    (u'walrus', 2),
    (u'penguin', 3),
    (u'walrus penguin', 1),
    (u'walrus -penguin', 1),
    (u'walrus -penguin #general #explicit', 1),
    (u'walrus -penguin #general #mature', 0),
    (u'-walrus +penguin', 2),
    (u'|walrus |penguin', 4),
    (u'+nothing |walrus |penguin', 0),
    (u'-nothing', 4),
])
def test_submission_search(db, term, n_results):
    user = db_utils.create_user()
    tag1 = db_utils.create_tag('walrus')
    tag2 = db_utils.create_tag('penguin')

    s1 = db_utils.create_submission(user, rating=ratings.GENERAL.code)
    db_utils.create_submission_tag(tag1, s1)
    db_utils.create_submission_tag(tag2, s1)

    s2 = db_utils.create_submission(user, rating=ratings.EXPLICIT.code)
    db_utils.create_submission_tag(tag1, s2)

    s3 = db_utils.create_submission(user, rating=ratings.GENERAL.code)
    db_utils.create_submission_tag(tag2, s3)

    s4 = db_utils.create_submission(user, rating=ratings.GENERAL.code)
    db_utils.create_submission_tag(tag2, s4)

    results, _, _ = search.select(
        search=search.Query.parse(term, 'submit'),
        userid=user, rating=ratings.EXPLICIT.code, limit=100,
        cat=None, subcat=None, within='', backid=None, nextid=None)

    assert len(results) == n_results


@pytest.mark.parametrize('rating', ratings.ALL_RATINGS)
@pytest.mark.parametrize('block_rating', ratings.ALL_RATINGS)
def test_search_blocked_tags(db, rating, block_rating):
    owner = db_utils.create_user()
    viewer = db_utils.create_user()

    allowed_tag = db_utils.create_tag('walrus')
    blocked_tag = db_utils.create_tag('penguin')

    db_utils.create_blocktag(viewer, blocked_tag, block_rating.code)

    s1 = db_utils.create_submission(owner, rating=rating.code)
    db_utils.create_submission_tag(allowed_tag, s1)
    db_utils.create_submission_tag(blocked_tag, s1)

    s2 = db_utils.create_submission(owner, rating=rating.code)
    db_utils.create_submission_tag(allowed_tag, s2)

    s3 = db_utils.create_submission(owner, rating=rating.code)
    db_utils.create_submission_tag(blocked_tag, s3)

    def check(term, n_results):
        results, _, _ = search.select(
            search=search.Query.parse(term, 'submit'),
            userid=viewer, rating=ratings.EXPLICIT.code, limit=100,
            cat=None, subcat=None, within='', backid=None, nextid=None)

        assert len(results) == n_results

    if rating < block_rating:
        check(u'walrus', 2)
        check(u'penguin', 2)
    else:
        check(u'walrus', 1)
        check(u'penguin', 0)


_page_limit = 6


@mock.patch.object(search, 'COUNT_LIMIT', 10)
def test_search_pagination(db):
    owner = db_utils.create_user()
    submissions = [db_utils.create_submission(owner, rating=ratings.GENERAL.code) for i in range(30)]
    tag = db_utils.create_tag('penguin')
    search_query = search.Query.parse(u'penguin', 'submit')

    for submission in submissions:
        db_utils.create_submission_tag(tag, submission)

    result, next_count, back_count = search.select(
        search=search_query,
        userid=owner, rating=ratings.EXPLICIT.code, limit=_page_limit,
        cat=None, subcat=None, within='', backid=None, nextid=None)

    assert back_count == 0
    assert next_count == search.COUNT_LIMIT
    assert [item['submitid'] for item in result] == submissions[:-_page_limit - 1:-1]

    result, next_count, back_count = search.select(
        search=search_query,
        userid=owner, rating=ratings.EXPLICIT.code, limit=_page_limit,
        cat=None, subcat=None, within='', backid=None, nextid=submissions[-_page_limit])

    assert back_count == _page_limit
    assert next_count == search.COUNT_LIMIT
    assert [item['submitid'] for item in result] == submissions[-_page_limit - 1:-2 * _page_limit - 1:-1]

    result, next_count, back_count = search.select(
        search=search_query,
        userid=owner, rating=ratings.EXPLICIT.code, limit=_page_limit,
        cat=None, subcat=None, within='', backid=submissions[_page_limit - 1], nextid=None)

    assert back_count == search.COUNT_LIMIT
    assert next_count == _page_limit
    assert [item['submitid'] for item in result] == submissions[2 * _page_limit - 1:_page_limit - 1:-1]


@pytest.mark.parametrize(['term', 'n_results'], [
    (u"shouldmatchnothing\\k", 0),
    (u"nobodyatall", 0),
    (u"JasonAG", 1),
    (u"Jason", 1),
    (u"rob", 1),
    (u"twisted", 2),
    (u"sam", 2),
    (u"jason otherkin", 2),
    (u"ryan wildlife calvin", 3),
    (u"Marth", 1),
])
def test_user_search(db, term, n_results):
    config = CharSettings({'use-only-tag-blacklist'}, {}, {})
    db_utils.create_user("Sam Peacock", username="sammy", config=config)
    db_utils.create_user("LionCub", username="spammer2800", config=config)
    db_utils.create_user("Samantha Wildlife", username="godall", config=config)
    db_utils.create_user("Ryan Otherkin", username="bball28", config=config)
    db_utils.create_user("Pawsome", username="pawsome", config=config)
    db_utils.create_user("Twisted Calvin", username="twistedcalvin", config=config)
    db_utils.create_user("JasonAG", username="robert", config=config)
    db_utils.create_user("Twisted Mindset", username="twistedm", config=config)
    db_utils.create_user("Martha", config=config)

    results = search.select_users(term)
    assert len(results) == n_results


def test_user_search_ordering(db):
    config = CharSettings({'use-only-tag-blacklist'}, {}, {})
    db_utils.create_user("user_aa", username="useraa", config=config)
    db_utils.create_user("user_ba", username="userba", config=config)
    db_utils.create_user("user_Ab", username="userab", config=config)
    db_utils.create_user("user_Bb", username="userbb", config=config)

    results = search.select_users(u"user")
    assert [user["title"] for user in results] == ["user_aa", "user_Ab", "user_ba", "user_Bb"]

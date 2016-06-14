import pytest

from libweasyl.models.helpers import CharSettings
from libweasyl import ratings
from weasyl.test import db_utils
from weasyl import search


def test_query_parsing():
    assert not search.Query.parse('', 'submit')
    assert not search.Query.parse('#character', 'submit')
    assert search.Query.parse('tag_that_does_not_exist', 'submit')

    query = search.Query.parse('one, two +three & -four |five |six user:a +user:b -user:c #general #moderate #submission', 'journal')

    assert query.possible_includes == {'five', 'six'}
    assert query.required_includes == {'one', 'two', 'three'}
    assert query.required_excludes == {'four'}
    assert query.required_user_includes == {'a', 'b'}
    assert query.required_user_excludes == {'c'}
    assert query.ratings == {ratings.GENERAL.code, ratings.MODERATE.code}
    assert query.find == 'submit'


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

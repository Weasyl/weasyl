import pytest

from libweasyl.models.helpers import CharSettings
from libweasyl import ratings
from weasyl.test import db_utils
from weasyl import search


def do_search(query, find):
    terms = {
        'cat': None, 'subcat': None, 'within': '', 'rated': [],
        'q': query, 'find': find, 'backid': None, 'nextid': None
    }
    return search.select(None, ratings.GENERAL.code, 100, **terms)


@pytest.mark.parametrize(['term', 'category', 'n_results'], [
    (u"shouldmatchnothing", "submit", 0),
    (u"shouldmatchnothing\\k", "user", 0),
    (u"nobodyatall", "user", 0),
    (u"JasonAG", "user", 1),
    (u"Jason", "user", 1),
    (u"rob", "user", 1),
    (u"twisted", "user", 2),
    (u"sam", "user", 2),
    (u"jason otherkin", "user", 2),
    (u"ryan wildlife calvin", "user", 3),
    (u"Marth", "user", 1),
])
def test_user_search(db, term, category, n_results):
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

    results, _, _ = do_search(term, category)
    assert len(results) == n_results


def test_user_search_ordering(db):
    config = CharSettings({'use-only-tag-blacklist'}, {}, {})
    db_utils.create_user("user_aa", username="useraa", config=config)
    db_utils.create_user("user_ba", username="userba", config=config)
    db_utils.create_user("user_Ab", username="userab", config=config)
    db_utils.create_user("user_Bb", username="userbb", config=config)

    results, _, _ = do_search(u"user", "user")
    assert [user["title"] for user in results] == ["user_aa", "user_Ab", "user_ba", "user_Bb"]

import pytest
from ada_url import URL
from pyramid.threadlocal import get_current_request

from libweasyl.models import content, users
from weasyl.test import db_utils
from weasyl import define as d


def l2dl(input_list, k='k'):
    "For list2dictlist."
    return [{k: x} for x in input_list]


pagination_tests = [
    ((l2dl([1, 2, 3]), False, False, 1, 'k'), (None, 1), l2dl([1])),
    ((l2dl([1, 2, 3]), False, False, 2, 'k'), (None, 2), l2dl([1, 2])),
    ((l2dl([1, 2, 3]), False, False, 3, 'k'), (None, None), l2dl([1, 2, 3])),
    ((l2dl([1, 2, 3]), True, False, 2, 'k'), (2, 3), l2dl([2, 3])),
    ((l2dl([1, 2, 3]), False, True, 2, 'k'), (1, 2), l2dl([1, 2])),
    ((l2dl([1, 2, 3, 4, 5]), False, False, 4, 'k'), (None, 4), l2dl([1, 2, 3, 4])),
    ((l2dl([1, 2, 3, 4, 5]), True, False, 4, 'k'), (2, 5), l2dl([2, 3, 4, 5])),
    ((l2dl([1, 2, 3, 4, 5]), False, True, 4, 'k'), (1, 4), l2dl([1, 2, 3, 4])),
    ((l2dl([1, 2, 3, 4, 5], k='k2'), False, False, 4, 'k2'), (None, 4), l2dl([1, 2, 3, 4], k='k2')),
    (([], False, False, 1, 'k'), (None, None), []),
    (([], True, False, 1, 'k'), (None, None), []),
    (([], False, True, 1, 'k'), (None, None), []),
]


@pytest.mark.parametrize(
    ('parameters', 'expected_pair', 'expected_rows'), pagination_tests)
def test_paginate(parameters, expected_pair, expected_rows):
    pair = d.paginate(*parameters)
    assert (pair, parameters[0]) == (expected_pair, expected_rows)


iso8601_tests = [
    (1392206700, '2014-02-12T17:05:00Z'),
    (1392206701, '2014-02-12T17:05:01Z'),
    (1392206760, '2014-02-12T17:06:00Z'),
]


@pytest.mark.parametrize(('parameter', 'expected'), iso8601_tests)
def test_iso8601(parameter, expected):
    assert d.iso8601(parameter) == expected


@pytest.mark.parametrize(('expected', 'parameter'), iso8601_tests)
def test_parse_iso8601(parameter, expected):
    assert d.parse_iso8601(parameter) == expected


def test_parse_iso8601_invalid_format():
    with pytest.raises(ValueError):
        d.parse_iso8601('dongs')


def create_with_user(func):
    def create_func():
        return func(db_utils.create_user())
    return create_func


view_things = [
    (create_with_user(db_utils.create_submission), content.Submission, 'submissions'),
    (create_with_user(db_utils.create_character), content.Character, 'characters'),
    (create_with_user(db_utils.create_journal), content.Journal, 'journals'),
    (db_utils.create_user, users.Profile, 'users'),
]


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_content_view(db, create_func, model, feature):
    """
    Viewing content increments its view count.
    """
    user = db_utils.create_user()
    thing = create_func()
    assert d.common_view_content(user, thing, feature) == 1
    assert db.query(model).get(thing).page_views == 1


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_content_view_twice(db, create_func, model, feature):
    """
    Two users viewing the same content increments the view count twice.
    """
    user1 = db_utils.create_user()
    user2 = db_utils.create_user()
    thing = create_func()
    assert d.common_view_content(user1, thing, feature) == 1
    assert d.common_view_content(user2, thing, feature) == 2
    assert db.query(model).get(thing).page_views == 2


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_content_view_same_user_twice(db, create_func, model, feature):
    """
    The same user viewing the same content twice does not increment the view
    count twice.
    """
    user = db_utils.create_user()
    thing = create_func()
    assert d.common_view_content(user, thing, feature) == 1
    assert d.common_view_content(user, thing, feature) is None
    assert db.query(model).get(thing).page_views == 1


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_content_view_same_user_twice_clearing_views(db, create_func, model, feature):
    """
    The same user viewing the same content twice *does* increment the view count
    twice iff the `views` table was truncated in between.
    """
    user = db_utils.create_user()
    thing = create_func()
    d.common_view_content(user, thing, feature)
    db.execute(d.meta.tables['views'].delete())
    assert d.common_view_content(user, thing, feature) == 2
    assert db.query(model).get(thing).page_views == 2


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_anonymous_content_view(db, create_func, model, feature):
    """
    Content viewed anonymously also increments the view count.
    """
    thing = create_func()
    assert d.common_view_content(0, thing, feature) == 1
    assert db.query(model).get(thing).page_views == 1


@pytest.mark.parametrize(('create_func', 'model', 'feature'), view_things)
def test_two_anonymous_content_views(db, create_func, model, feature):
    """
    Two anonymous users coming from different IPs will both increment the view
    count separately.
    """
    thing = create_func()
    d.common_view_content(0, thing, feature)
    get_current_request().client_addr = '127.0.0.2'
    assert d.common_view_content(0, thing, feature) == 2
    assert db.query(model).get(thing).page_views == 2


def test_viewing_own_profile(db):
    """
    Viewing one's own profile does not increment the view count.
    """
    user = db_utils.create_user()
    assert d.common_view_content(user, user, 'users') is None
    assert db.query(users.Profile).get(user).page_views == 0


def test_nul():
    with pytest.raises(ValueError) as err:
        d.engine.scalar("SELECT %(test)s", test="foo\x00bar")

    assert err.value.args == ("A string literal cannot contain NUL (0x00) characters.",)


@pytest.mark.parametrize(("input", "output"), [
    ("example.com/foo", "https://example.com/foo"),
    ("//example.com/foo", "https://example.com/foo"),
    ("http://example.com/foo", "http://example.com/foo"),
    ("https://example.com", "https://example.com/"),
    ("https://example.com/foo?bar=baz#quux", "https://example.com/foo?bar=baz#quux"),
    ("https://www.weаsyl.com/foo", "https://www.xn--wesyl-5ve.com/foo"),
    ("\xa0 \xa0example\t.com\r\n", "https://example.com/"),
])
def test_text_fix_url_valid(input, output):
    result = d.text_fix_url(input)
    assert isinstance(result, URL)
    assert result.href == output


@pytest.mark.parametrize("input", [
    "javascript:alert(1)",
    "data:text/plain,foo",
    "https://localhost/",
    "https://localhost./",
    "https://example.com.",
    "https://bar:baz@example.com/foo",
    "/view/123",
])
def test_text_fix_url_invalid(input):
    assert d.text_fix_url(input) is None

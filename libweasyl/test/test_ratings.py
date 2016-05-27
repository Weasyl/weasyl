from operator import ne, lt, le, gt, ge

import pytest

from libweasyl import ratings


@pytest.mark.parametrize(('age', 'expected'), [
    (-1, [ratings.GENERAL]),
    (0, [ratings.GENERAL]),
    (12, [ratings.GENERAL]),
    (13, [ratings.GENERAL, ratings.MODERATE]),
    (17, [ratings.GENERAL, ratings.MODERATE]),
    (18, ratings.ALL_RATINGS),
    (21, ratings.ALL_RATINGS),
])
def test_get_ratings_for_age(age, expected):
    assert ratings.get_ratings_for_age(age) == expected


@pytest.mark.parametrize(('rating', 'expected'), [
    (ratings.GENERAL, "General"),
    (ratings.MODERATE, "Moderate (13+)"),
    (ratings.MATURE, "Mature (18+ non-sexual)"),
    (ratings.EXPLICIT, "Explicit (18+ sexual)"),
])
def test_name_with_age(rating, expected):
    assert rating.name_with_age == expected


@pytest.mark.parametrize('rating', ratings.ALL_RATINGS)
def test_equality(rating):
    assert rating == rating


@pytest.mark.parametrize(('r1', 'op', 'r2'), [
    (ratings.GENERAL, ne, ratings.MODERATE),
    (ratings.GENERAL, lt, ratings.MODERATE),
    (ratings.MODERATE, gt, ratings.GENERAL),
    (ratings.GENERAL, ge, ratings.GENERAL),
    (ratings.GENERAL, le, ratings.GENERAL),
])
def test_comparisons(r1, op, r2):
    assert op(r1, r2)


def test_hashability():
    assert hash(ratings.GENERAL) != hash(ratings.MODERATE)

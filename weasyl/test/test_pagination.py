import unittest

import pytest

import weasyl.pagination as pagination
from weasyl.pagination import (
    FIRST_PAGE,
    PrevFilter,
    NextFilter,
    paginate,
)


ID_FIELD = 'id_field'


def fake_result(id):
    return {ID_FIELD: id}


def fake_results(ids):
    return [fake_result(id) for id in ids]


class PaginationTestCase(unittest.TestCase):
    def test_simple_case(self):
        result_size = 10
        check_limit = 20
        extra_value = "hello"

        def select_list(a, b, c, limit, backid=None, nextid=None, extra=None):
            self.assertEqual(extra_value, extra)
            self.assertEqual(check_limit, limit)
            return fake_results(range(result_size))

        def select_count(a, b, c, backid=None, nextid=None, extra=None):
            self.assertEqual(extra_value, extra)
            if backid is not None:
                return backid
            if nextid is not None:
                return nextid
            # should get one or the other
            raise ValueError()

        result = pagination.PaginatedResult(select_list, select_count, ID_FIELD, "%s",
                                            1, 2, 3, limit=check_limit, extra=extra_value)
        self.assertEqual(result_size - 1, result.next_count)
        self.assertEqual(0, result.back_count)
        self.assertEqual(result_size, len(result.query))
        self.assertEqual("nextid=" + str(result_size - 1), result.next_url)


def _l2dl(xs):
    return [{"k": x} for x in xs]


@pytest.mark.parametrize(
    (   "ids",    "limit", "page",          "expected_prev", "expected_next", "expected_ids"),
    [
        ([1, 2],       1,   FIRST_PAGE,      None,            NextFilter(1),   [1]),
        ([1, 2, 3],    2,   FIRST_PAGE,      None,            NextFilter(2),   [1, 2]),
        ([1, 2, 3],    3,   FIRST_PAGE,      None,            None,            [1, 2, 3]),
        ([3, 2, 1],    3,   PrevFilter(...), None,            NextFilter(3),   [1, 2, 3]),
        ([1, 2, 3],    3,   NextFilter(...), PrevFilter(1),   None,            [1, 2, 3]),
        ([3, 2, 1],    2,   PrevFilter(...), PrevFilter(2),   NextFilter(3),   [2, 3]),
        ([1, 2, 3],    2,   NextFilter(...), PrevFilter(1),   NextFilter(2),   [1, 2]),
        ([],           1,   FIRST_PAGE,      None,            None,            []),
        ([],           1,   PrevFilter(...), None,            None,            []),
        ([],           1,   NextFilter(...), None,            None,            []),
    ],
)
def test_paginate(ids, limit, page, expected_prev, expected_next, expected_ids):
    items = _l2dl(ids)
    prev_page, next_page = paginate(items, limit=limit, page=page, key="k")
    assert (prev_page, next_page, items) == (expected_prev, expected_next, _l2dl(expected_ids))

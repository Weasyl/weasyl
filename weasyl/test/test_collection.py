import unittest
from dataclasses import dataclass

import pytest

from libweasyl import ratings

from weasyl.error import WeasylError
from weasyl.test import db_utils
from weasyl import collection


@dataclass(frozen=True, slots=True)
class Counts:
    active: int
    pending: int


def _test_decide_unrelated(decide):
    def test(self):
        """
        A user should not be able to accept or reject a request or offer for a collection that they’ve neither requested nor offered.
        """
        self.request()
        self.assertEqual(Counts(0, 1), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

        decide(self.other, [(self.s, self.collector)])

        self.assertEqual(Counts(0, 1), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

        collection.pending_reject(self.creator, [(self.s, self.collector)])

        self.offer()
        self.assertEqual(Counts(0, 0), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))

        decide(self.other, [(self.s, self.collector)])

        self.assertEqual(Counts(0, 0), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))

    return test


@pytest.mark.usefixtures('db')
class CollectionsTestCase(unittest.TestCase):
    def setUp(self):
        self.creator = db_utils.create_user()
        self.collector = db_utils.create_user()
        self.other = db_utils.create_user()
        self.s = db_utils.create_submission(self.creator)

    def offer(self):
        collection.offer(self.creator, self.s, self.collector)

    def request(self):
        collection.request(self.collector, self.s, self.creator)

    def count_collections(self, userid):
        return Counts(*(collection.select_count(
            userid=userid,
            rating=ratings.GENERAL.code,
            otherid=userid,
            pending=pending,
        ) for pending in (False, True)))

    def test_offer_and_accept(self):
        self.offer()
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))
        collection.pending_accept(self.collector, [(self.s, self.collector)])
        self.assertEqual(Counts(1, 0), self.count_collections(self.collector))

    def test_offer_with_errors(self):
        self.assertRaises(WeasylError, collection.offer,
                          db_utils.create_user(), self.s, self.collector)

    def test_offer_and_reject(self):
        self.offer()
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))
        collection.pending_reject(self.collector, [(self.s, self.collector)])
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

    def test_offer_accept_and_remove(self):
        self.offer()
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))
        collection.pending_accept(self.collector, [(self.s, self.collector)])
        collection.remove(self.collector, [self.s])
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

    def test_offer_and_impersonate_accept(self):
        """
        A user should not be able to approve their own collection offer.
        """
        self.offer()
        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))

        collection.pending_accept(self.creator, [(self.s, self.collector)])

        self.assertEqual(Counts(0, 1), self.count_collections(self.collector))

    def test_request_and_accept(self):
        self.request()
        self.assertEqual(Counts(0, 1), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

        collection.pending_accept(self.creator, [(self.s, self.collector)])

        self.assertEqual(Counts(0, 0), self.count_collections(self.creator))
        self.assertEqual(Counts(1, 0), self.count_collections(self.collector))

    def test_request_and_impersonate_accept(self):
        """
        A user should not be able to approve their own collection request.
        """
        self.request()
        self.assertEqual(Counts(0, 1), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

        collection.pending_accept(self.collector, [(self.s, self.collector)])

        self.assertEqual(Counts(0, 1), self.count_collections(self.creator))
        self.assertEqual(Counts(0, 0), self.count_collections(self.collector))

    # `unittest.TestCase` style doesn’t support `pytest.mark.parametrize`
    test_accept_unrelated = _test_decide_unrelated(collection.pending_accept)
    test_reject_unrelated = _test_decide_unrelated(collection.pending_reject)

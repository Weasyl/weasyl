import unittest
import pytest

from libweasyl import ratings

from weasyl.error import WeasylError
from weasyl.test import db_utils
from weasyl import collection


@pytest.mark.usefixtures('db')
class CollectionsTestCase(unittest.TestCase):
    def setUp(self):
        self.creator = db_utils.create_user()
        self.collector = db_utils.create_user()
        self.s = db_utils.create_submission(self.creator)

    def offer(self):
        collection.offer(self.creator, self.s, self.collector)

    def count_collections(self, pending, rating=ratings.GENERAL.code):
        return len(collection.select_manage(self.collector, rating, 10, pending))

    def test_offer_and_accept(self):
        self.offer()
        self.assertEqual(1, self.count_collections(True))
        collection.pending_accept(self.collector, [(self.s, self.collector)])
        self.assertEqual(1, self.count_collections(False))

    def test_offer_with_errors(self):
        self.assertRaises(WeasylError, collection.offer,
                          db_utils.create_user(), self.s, self.collector)

    def test_offer_and_reject(self):
        self.offer()
        self.assertEqual(1, self.count_collections(True))
        collection.pending_reject(self.collector, [(self.s, self.collector)])
        self.assertEqual(0, self.count_collections(False))
        self.assertEqual(0, self.count_collections(True))

    def test_offer_accept_and_remove(self):
        self.offer()
        self.assertEqual(1, self.count_collections(True))
        collection.pending_accept(self.collector, [(self.s, self.collector)])
        collection.remove(self.collector, [self.s])
        self.assertEqual(0, self.count_collections(False))
        self.assertEqual(0, self.count_collections(True))

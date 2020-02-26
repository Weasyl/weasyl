from __future__ import absolute_import

import unittest
import pytest

from libweasyl import ratings

from weasyl.test import db_utils
from weasyl import favorite


@pytest.mark.usefixtures('db')
class SelectSubmissionCountTestCase(unittest.TestCase):
    def setUp(self):
        self.user1 = db_utils.create_user()
        self.user2 = db_utils.create_user()
        self.count = 20
        self.pivot = 5
        s = db_utils.create_submissions(self.count, self.user1, ratings.GENERAL.code)
        self.pivotid = s[self.pivot]
        f = []
        time = 100
        for submitid in s:
            time = time + 1
            f.append(db_utils.create_favorite(self.user2, submitid=submitid))

    def test_count_backid(self):
        self.assertEqual(
            self.count - self.pivot - 1,
            favorite.select_submit_count(self.user1, ratings.GENERAL.code,
                                         otherid=self.user2, backid=self.pivotid))

    def test_count_nextid(self):
        self.assertEqual(
            self.pivot,
            favorite.select_submit_count(self.user1, ratings.GENERAL.code,
                                         otherid=self.user2, nextid=self.pivotid))

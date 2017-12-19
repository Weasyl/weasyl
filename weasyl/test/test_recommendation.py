from __future__ import absolute_import

import unittest
import pytest

from weasyl import define as d
from weasyl import recommendation as rec
from weasyl.error import WeasylError
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
class RecommendationTestCase(unittest.TestCase):
    def setUp(self):
        self.userid = db_utils.create_user()
        self.submitid = db_utils.create_submission(userid=db_utils.create_user())

    def ratingCount(self):
        return d.engine.scalar("SELECT COUNT(*) FROM recommendation_rating"
                               " WHERE userid=%(userid)s AND submitid=%(submitid)s",
                               userid=self.userid, submitid=self.submitid)

    def test_invalid_rec_rating(self):
        "Invalid ratings throw an exception."
        with pytest.raises(WeasylError):
            rec.set_user_rating(self.userid, self.submitid, 6)

    def test_set_and_clear(self):
        "There is never more than one rating per (user, submission)"
        assert 0 == self.ratingCount()
        rec.set_user_rating(self.userid, self.submitid, rec.RecommendationRating.LIKE)
        assert 1 == self.ratingCount()
        rec.clear_user_rating(self.userid, self.submitid)
        assert 0 == self.ratingCount()
        rec.set_user_rating(self.userid, self.submitid, rec.RecommendationRating.LIKE)
        rec.set_user_rating(self.userid, self.submitid, rec.RecommendationRating.FAVORITE)
        assert 1 == self.ratingCount()

    def test_get(self):
        assert rec.get_user_rating(self.userid, self.submitid) is None
        rec.set_user_rating(self.userid, self.submitid, rec.RecommendationRating.LIKE)
        assert rec.get_user_rating(self.userid, self.submitid) is rec.RecommendationRating.LIKE
import unittest
import pytest

from libweasyl import ratings

from weasyl.test import db_utils
from weasyl import character


@pytest.mark.usefixtures('db')
class SelectCountTestCase(unittest.TestCase):
    def setUp(self):
        self.user1 = db_utils.create_user()
        self.user2 = db_utils.create_user()
        self.friend1 = db_utils.create_user()
        db_utils.create_friendship(self.user1, self.friend1)
        self.count = 20
        self.pivot = 5
        s = db_utils.create_characters(self.count, self.user1, ratings.GENERAL.code)
        self.pivotid = s[self.pivot]

    def test_count_backid(self):
        self.assertEqual(
            self.count - self.pivot - 1,
            character.select_count(self.user1, ratings.GENERAL.code, backid=self.pivotid))

    def test_count_nextid(self):
        self.assertEqual(
            self.pivot,
            character.select_count(self.user1, ratings.GENERAL.code, nextid=self.pivotid))

    def test_see_friends_character(self):
        """
        Should be able to see a friend's friends-only character in a listing.
        """
        c = db_utils.create_character(self.friend1, friends_only=True)
        self.assertEqual(
            self.count + 1,
            character.select_count(self.user1, ratings.GENERAL.code))
        self.assertEqual(
            c,
            character.select_list(self.user1, ratings.GENERAL.code, 100)[0]['charid'])

    def test_cannot_see_non_friends_character(self):
        """
        Should not be able to see a non-friend's friends-ony character in a listing.
        """
        db_utils.create_character(self.user2, friends_only=True)
        self.assertEqual(
            self.count,
            character.select_count(self.user1, ratings.GENERAL.code))

    def test_can_see_own_blocktag_character(self):
        """
        Can see your own character in a listing even with a blocked tag.
        """
        block_tagid = db_utils.create_tag("blocked")
        db_utils.create_blocktag(self.user1, block_tagid, ratings.GENERAL.code)
        charid = db_utils.create_character(self.user1, name="My blocktag character")
        db_utils.create_character_tag(block_tagid, charid)
        # A journal that we should NOT see.
        other_charid = db_utils.create_character(self.user2, name="Other user's blocktag character")
        db_utils.create_character_tag(block_tagid, other_charid)
        self.assertEqual(
            charid,
            character.select_list(self.user1, ratings.GENERAL.code, 100)[0]['charid'])

    def test_can_see_own_rating_character(self):
        """
        Can see your own character in a listing even when it's above your max rating.
        """
        charid = db_utils.create_character(self.user1, rating=ratings.EXPLICIT.code)
        db_utils.create_character(self.user2, rating=ratings.EXPLICIT.code)
        self.assertEqual(
            charid,
            character.select_list(self.user1, ratings.GENERAL.code, 100)[0]['charid'])

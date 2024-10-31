import unittest
import pytest

from libweasyl import ratings

from weasyl.test import db_utils
from weasyl import journal


def select_user_count(userid, rating, **kwargs):
    return len(journal.select_user_list(userid, rating, limit=1000, **kwargs))


@pytest.mark.usefixtures('db')
class SelectUserCountTestCase(unittest.TestCase):
    def setUp(self):
        self.user1 = db_utils.create_user()
        self.user2 = db_utils.create_user()
        self.friend1 = db_utils.create_user()
        db_utils.create_friendship(self.user1, self.friend1)
        self.count = 20
        self.pivot = 5
        s = db_utils.create_journals(self.count, self.user1, ratings.GENERAL.code)
        self.pivotid = s[self.pivot]

    def test_count_backid(self):
        self.assertEqual(
            self.count - self.pivot - 1,
            select_user_count(self.user1, ratings.GENERAL.code, backid=self.pivotid))

    def test_count_nextid(self):
        self.assertEqual(
            self.pivot,
            select_user_count(self.user1, ratings.GENERAL.code, nextid=self.pivotid))

    def test_see_friends_journal(self):
        """
        Should be able to see a friend's journal in a listing.
        """
        j = db_utils.create_journal(self.friend1, 'Friends only journal', friends_only=True)
        self.assertEqual(
            self.count + 1,
            select_user_count(self.user1, ratings.GENERAL.code))
        self.assertEqual(
            j,
            journal.select_user_list(self.user1, ratings.GENERAL.code, 100)[0]['journalid'])

    def test_cannot_see_non_friends_journal(self):
        """
        Should not be able to see a non-friend's journal in a listing.
        """
        db_utils.create_journal(self.user2, 'Friends only journal', friends_only=True)
        self.assertEqual(
            self.count,
            select_user_count(self.user1, ratings.GENERAL.code))

    def test_can_see_own_blocktag_journal(self):
        """
        Can see your own journal in a listing even with a blocked tag.
        """
        block_tagid = db_utils.create_tag("blocked")
        db_utils.create_blocktag(self.user1, block_tagid, ratings.GENERAL.code)
        journalid = db_utils.create_journal(self.user1, "My blocktag journal")
        db_utils.create_journal_tag(block_tagid, journalid)
        # A journal that we should NOT see.
        other_journalid = db_utils.create_journal(self.user2, "Other user's blocktag journal")
        db_utils.create_journal_tag(block_tagid, other_journalid)
        self.assertEqual(
            journalid,
            journal.select_user_list(self.user1, ratings.GENERAL.code, 100)[0]['journalid'])

    def test_can_see_own_rating_journal(self):
        """
        Can see your own journal in a listing even when it's above your max rating.
        """
        my_journalid = db_utils.create_journal(self.user1, rating=ratings.EXPLICIT.code)
        db_utils.create_journal(self.user2, rating=ratings.EXPLICIT.code)
        self.assertEqual(
            my_journalid,
            journal.select_user_list(self.user1, ratings.GENERAL.code, 100)[0]['journalid'])

    def test_remove(self):
        j1 = db_utils.create_journal(self.user1, rating=ratings.GENERAL.code)
        j2 = db_utils.create_journal(self.user1, rating=ratings.GENERAL.code)

        journal.remove(self.user1, j1)

        user_list = journal.select_user_list(self.user1, ratings.GENERAL.code, 100)

        self.assertEqual(self.count + 1, len(user_list))
        self.assertEqual(j2, user_list[0]['journalid'])

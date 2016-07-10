import datetime
import unittest
import pytest

import arrow
import web

from libweasyl.models.helpers import CharSettings
from libweasyl import ratings

from libweasyl.models import site, users
import weasyl.define as d
from weasyl import blocktag, searchtag, submission, welcome
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
class SelectListTestCase(unittest.TestCase):
    def test_ratings(self):
        # Create a bunch of submissions with different ratings, check counts
        # Check that a user will see their own submissions even if the rating is off
        # Check that non-logged-in user will see only general ratings.
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        db_utils.create_submission(user1, rating=ratings.GENERAL.code)
        db_utils.create_submission(user1, rating=ratings.MODERATE.code)
        db_utils.create_submission(user1, rating=ratings.MATURE.code)
        db_utils.create_submission(user1, rating=ratings.EXPLICIT.code)
        self.assertEqual(4, len(submission.select_list(user2, ratings.EXPLICIT.code, 10, config="l")))
        self.assertEqual(3, len(submission.select_list(user2, ratings.MATURE.code, 10, config="l")))
        self.assertEqual(2, len(submission.select_list(user2, ratings.MODERATE.code, 10, config="l")))
        self.assertEqual(1, len(submission.select_list(user2, ratings.GENERAL.code, 10, config="l")))

        # A user sees their own submissions regardless of the rating level
        self.assertEqual(4, len(submission.select_list(
            user1, ratings.GENERAL.code, 10, otherid=user1)))

    def test_ratings_twittercard(self):
        # For tests, this isn't set. absolutify_url requires it,
        # so this test would fail if it wasn't set.
        web.ctx.realhome = 'https://lo.weasyl.com:8443'

        user = db_utils.create_user()

        sub1 = db_utils.create_submission(user, rating=ratings.GENERAL.code)
        sub2 = db_utils.create_submission(user, rating=ratings.MODERATE.code)
        sub3 = db_utils.create_submission(user, rating=ratings.MATURE.code)
        sub4 = db_utils.create_submission(user, rating=ratings.EXPLICIT.code)

        card1 = submission.twitter_card(sub1)
        card2 = submission.twitter_card(sub2)
        card3 = submission.twitter_card(sub3)
        card4 = submission.twitter_card(sub4)

        self.assertNotEqual('This image is rated 18+ and only viewable on weasyl.com', card1['description'])
        self.assertNotEqual('This image is rated 18+ and only viewable on weasyl.com', card2['description'])
        self.assertEqual('This image is rated 18+ and only viewable on weasyl.com', card3['description'])
        self.assertEqual('This image is rated 18+ and only viewable on weasyl.com', card4['description'])

        # Delete this so it cannot interfere with other things.
        del web.ctx.realhome

    def test_filters(self):
        # Test filters of the following:
        # userid, folderid, category, hidden
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        folder = db_utils.create_folder(user1)
        db_utils.create_submission(user1, rating=ratings.GENERAL.code, folderid=folder)
        db_utils.create_submission(user1, rating=ratings.GENERAL.code, subtype=1010)
        db_utils.create_submission(user1, rating=ratings.GENERAL.code, settings=CharSettings({'hidden'}, {}, {}))
        db_utils.create_submission(user2, rating=ratings.GENERAL.code)

        self.assertEqual(3, len(submission.select_list(user1, ratings.EXPLICIT.code, 10)))
        self.assertEqual(1, len(submission.select_list(user1, ratings.EXPLICIT.code, 10, otherid=user2)))
        self.assertEqual(1, len(submission.select_list(user1, ratings.EXPLICIT.code, 10, folderid=folder)))
        self.assertEqual(1, len(submission.select_list(user1, ratings.EXPLICIT.code, 10, subcat=1010)))

    def test_select_list_limits(self):
        user1 = db_utils.create_user()
        submissions = db_utils.create_submissions(
            20, user1, rating=ratings.GENERAL.code)

        results = submission.select_list(user1, ratings.EXPLICIT.code, 10)
        # submissions are descending, so we get the highest numbers first
        self.assertEqual(submissions[19], results[0]['submitid'])
        self.assertEqual(10, len(results))

        results = submission.select_list(
            user1, ratings.EXPLICIT.code, 10, nextid=submissions[10])
        self.assertEqual(submissions[9], results[0]['submitid'])

        results = submission.select_list(
            user1, ratings.EXPLICIT.code, 10, backid=submissions[10])
        self.assertEqual(submissions[19], results[0]['submitid'])

    def test_friends_only(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        db_utils.create_submission(user1, rating=ratings.GENERAL.code, settings=CharSettings({'friends-only'}, {}, {}))

        # poster can view their submission
        self.assertEqual(
            1, len(submission.select_list(user1, ratings.GENERAL.code, 10)))

        # but a non-friend or a non-logged in user cannot
        self.assertEqual(
            0, len(submission.select_list(None, ratings.GENERAL.code, 10)))
        self.assertEqual(
            0, len(submission.select_list(user2, ratings.GENERAL.code, 10)))

        # user with a pending friendship cannot view
        db_utils.create_friendship(user1, user2, settings=CharSettings({'pending'}, {}, {}))
        self.assertEqual(
            0, len(submission.select_list(user2, ratings.GENERAL.code, 10)))

        # but a friend can
        d.sessionmaker().query(users.Friendship).delete()
        db_utils.create_friendship(user1, user2)
        self.assertEqual(
            1, len(submission.select_list(user2, ratings.GENERAL.code, 10)))

    def test_ignored_user(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        db_utils.create_submission(user1, rating=ratings.GENERAL.code)
        # can view the submission
        self.assertEqual(
            1, len(submission.select_list(user2, ratings.GENERAL.code, 10)))
        # user2 blocks user1
        db_utils.create_ignoreuser(user2, user1)
        # user2 can no longer view the submission
        self.assertEqual(
            0, len(submission.select_list(user2, ratings.GENERAL.code, 10)))
        # but a non-logged in user can
        self.assertEqual(
            1, len(submission.select_list(None, ratings.GENERAL.code, 10)))

    def test_blocked_tag(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()

        # submission s1 has a walrus in it, but user2 does not like walruses
        s1 = db_utils.create_submission(user1, rating=ratings.GENERAL.code)
        tag1 = db_utils.create_tag("walrus")
        db_utils.create_submission_tag(tag1, s1)
        db_utils.create_blocktag(user2, tag1, ratings.GENERAL.code)
        self.assertEqual(
            0, len(submission.select_list(user2, ratings.GENERAL.code, 10)))

        # submission s2 has a penguin in it. user2 does not want to see penguins in
        # adult circumstances, but s2 is general, so visibility is OK
        s2 = db_utils.create_submission(user1, rating=ratings.GENERAL.code)
        tag2 = db_utils.create_tag("penguin")
        db_utils.create_submission_tag(tag2, s2)
        db_utils.create_blocktag(user2, tag2, ratings.EXPLICIT.code)
        self.assertEqual(
            1, len(submission.select_list(user2, ratings.EXPLICIT.code, 10)))

        # submission s3 has penguins on it in adult situations, but User2
        # is okay with that if it's one of User2's own submissions.
        s3 = db_utils.create_submission(user2, rating=ratings.EXPLICIT.code)
        db_utils.create_submission_tag(tag2, s3)
        self.assertEqual(
            2, len(submission.select_list(user2, ratings.EXPLICIT.code, 10)))

    def test_duplicate_blocked_tag(self):
        user = db_utils.create_user()
        blocktag.insert(user, title="orange", rating=ratings.GENERAL.code, tagid=None)
        blocktag.insert(user, title="orange", rating=ratings.GENERAL.code, tagid=None)

    def test_profile_page_filter(self):
        user1 = db_utils.create_user()
        folder = db_utils.create_folder(
            user1, settings=CharSettings({"profile-filter"}, {}, {}))
        db_utils.create_submissions(9, user1, ratings.GENERAL.code)
        db_utils.create_submission(user1, ratings.GENERAL.code, folderid=folder)
        self.assertEqual(
            10, len(submission.select_list(user1, ratings.GENERAL.code, 10)))
        self.assertEqual(
            9, len(submission.select_list(user1, ratings.GENERAL.code, 10,
                                          profile_page_filter=True)))

    def test_index_page_filter(self):
        user1 = db_utils.create_user()
        folder = db_utils.create_folder(
            user1, settings=CharSettings({"index-filter"}, {}, {}))
        db_utils.create_submissions(9, user1, ratings.GENERAL.code)
        db_utils.create_submission(user1, ratings.GENERAL.code, folderid=folder)
        self.assertEqual(
            10, len(submission.select_list(user1, ratings.GENERAL.code, 10)))
        self.assertEqual(
            9, len(submission.select_list(user1, ratings.GENERAL.code, 10,
                                          index_page_filter=True)))

    def test_feature_page_filter(self):
        user1 = db_utils.create_user()
        folder = db_utils.create_folder(
            user1, settings=CharSettings({"featured-filter"}, {}, {}))
        db_utils.create_submissions(9, user1, ratings.GENERAL.code)
        db_utils.create_submission(user1, ratings.GENERAL.code, folderid=folder)
        self.assertEqual(
            10, len(submission.select_list(user1, ratings.GENERAL.code, 10)))
        self.assertEqual(
            1, len(submission.select_list(user1, ratings.GENERAL.code, 10,
                                          featured_filter=True)))

    def test_retag(self):
        owner = db_utils.create_user()
        tagger = db_utils.create_user()
        s = db_utils.create_submission(owner, rating=ratings.GENERAL.code)

        searchtag.associate(owner, {'orange'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['orange'])

        searchtag.associate(tagger, {'apple', 'tomato'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['apple', 'tomato'])

        searchtag.associate(tagger, {'tomato'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['tomato'])

        searchtag.associate(owner, {'kale'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['kale'])

    def test_retag_no_owner_remove(self):
        config = CharSettings({'disallow-others-tag-removal'}, {}, {})
        owner = db_utils.create_user(config=config)
        tagger = db_utils.create_user()
        s = db_utils.create_submission(owner, rating=ratings.GENERAL.code)

        searchtag.associate(owner, {'orange'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['orange'])

        searchtag.associate(tagger, {'apple', 'tomato'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['apple', 'orange', 'tomato'])

        searchtag.associate(tagger, {'tomato'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['orange', 'tomato'])

        searchtag.associate(owner, {'kale'}, submitid=s)
        self.assertEqual(
            submission.select_view(owner, s, ratings.GENERAL.code)['tags'],
            ['kale'])

    def test_recently_popular(self):
        owner = db_utils.create_user()
        now = arrow.now()

        sub1 = db_utils.create_submission(owner, rating=ratings.GENERAL.code, unixtime=now - datetime.timedelta(days=6))
        sub2 = db_utils.create_submission(owner, rating=ratings.GENERAL.code, unixtime=now - datetime.timedelta(days=4))
        sub3 = db_utils.create_submission(owner, rating=ratings.GENERAL.code, unixtime=now - datetime.timedelta(days=2))
        sub4 = db_utils.create_submission(owner, rating=ratings.GENERAL.code, unixtime=now)
        tag = db_utils.create_tag(u'tag')

        for s in [sub1, sub2, sub3, sub4]:
            db_utils.create_submission_tag(tag, s)

        for i in range(100):
            favoriter = db_utils.create_user()
            db_utils.create_favorite(favoriter, sub2, 's', unixtime=now)

        recently_popular = submission.select_recently_popular()

        self.assertEqual(
            [item['submitid'] for item in recently_popular],
            [sub2, sub4, sub3, sub1])


@pytest.mark.usefixtures('db')
class SelectCountTestCase(unittest.TestCase):

    def setUp(self):
        self.user1 = db_utils.create_user()
        self.count = 20
        self.pivot = 5
        s = db_utils.create_submissions(self.count, self.user1, ratings.GENERAL.code)
        self.pivotid = s[self.pivot]

    def test_count(self):
        self.assertEqual(
            self.count, submission.select_count(self.user1, ratings.GENERAL.code))

    def test_count_backid(self):
        self.assertEqual(self.count - self.pivot - 1,
                         submission.select_count(self.user1, ratings.GENERAL.code, backid=self.pivotid))

    def test_count_nextid(self):
        self.assertEqual(self.pivot, submission.select_count(self.user1, ratings.GENERAL.code, nextid=self.pivotid))


@pytest.mark.usefixtures('db')
class SubmissionNotificationsTestCase(unittest.TestCase):
    """
    Tests related to submission notifications.

    TODO: Add additional tests here beyond friends-only.
    """
    def setUp(self):
        # userid of the owner of a submission.
        self.owner = db_utils.create_user()

        # userid of a friended follower.
        self.friend = db_utils.create_user()
        db_utils.create_follow(self.friend, self.owner)
        db_utils.create_friendship(self.owner, self.friend)

        # userid of a non-friended follower.
        self.nonfriend = db_utils.create_user()
        db_utils.create_follow(self.nonfriend, self.owner)

        # userid of an ignored follower.
        self.ignored = db_utils.create_user()
        db_utils.create_follow(self.ignored, self.owner)
        db_utils.create_ignoreuser(self.owner, self.ignored)

    def _notification_count(self, userid):
        return (
            d.connect().query(site.SavedNotification)
            .filter(site.SavedNotification.userid == userid)
            .count())

    def test_simple_submission(self):
        """
        Posting a submission should create notifications for all watchers.
        """
        s = db_utils.create_submission(self.owner)
        welcome.submission_insert(self.owner, s)
        self.assertEquals(1, self._notification_count(self.friend))
        self.assertEquals(1, self._notification_count(self.nonfriend))
        self.assertEquals(1, self._notification_count(self.ignored))

    def test_friends_only_submission(self):
        """
        Submissions uploaded as friends-only should be visible only to friends.
        """
        s = db_utils.create_submission(
            self.owner,
            settings=CharSettings({'friends-only'}, {}, {}))
        welcome.submission_insert(self.owner, s, settings='f')
        self.assertEquals(1, self._notification_count(self.friend))
        self.assertEquals(0, self._notification_count(self.nonfriend))
        self.assertEquals(0, self._notification_count(self.ignored))

    def test_submission_becomes_friends_only(self):
        """
        Submissions becoming friends-only should be removed from non-friends'
        notification lists.
        """
        # Initial behavior should match with normal.
        s = db_utils.create_submission(self.owner)
        welcome.submission_insert(self.owner, s)
        self.assertEquals(1, self._notification_count(self.friend))
        self.assertEquals(1, self._notification_count(self.nonfriend))
        self.assertEquals(1, self._notification_count(self.ignored))

        welcome.submission_became_friends_only(s, self.owner)
        self.assertEquals(1, self._notification_count(self.friend))
        self.assertEquals(0, self._notification_count(self.nonfriend))
        self.assertEquals(0, self._notification_count(self.ignored))

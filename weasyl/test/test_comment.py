import pytest
import unittest

from libweasyl import staff
from libweasyl.models import site

from weasyl import define as d
from weasyl import comment
from weasyl import shout
from weasyl.error import WeasylError
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
class TestRemoveComment:
    generation_parameters = [
        ("submit", db_utils.create_submission_comment, comment.remove,
         db_utils.create_submission),
        ("journal", db_utils.create_journal_comment, comment.remove,
         db_utils.create_journal),
        ("char", db_utils.create_character_comment, comment.remove,
         db_utils.create_character),
        (None, db_utils.create_shout, shout.remove, db_utils.create_shout),
    ]

    @pytest.fixture(autouse=True, params=generation_parameters)
    def setUp(self, request, monkeypatch):
        # userid of owner of the journal/submission/character
        self.owner = db_utils.create_user()
        # userid of the comment poster
        self.commenter = db_utils.create_user()
        # userid of a moderator
        self.moderator = db_utils.create_user()
        # userid of another user who isn't a moderator
        self.another_user = db_utils.create_user()
        # mock out staff.MODS
        monkeypatch.setattr(staff, 'MODS', {self.moderator})

        (self.feature, self.create_function, self.remove_function, call) = request.param
        self.target = call(self.owner) if self.feature is not None else self.owner
        self.commentid = self.create_function(self.commenter, self.target)
        self.args = {'commentid': self.commentid}
        if self.feature is not None:
            self.args['feature'] = self.feature

    def test_commenter_can_remove(self):
        assert self.target == self.remove_function(self.commenter, **self.args)

    def test_commenter_can_not_remove_with_replies(self):
        # reply to the existing comment
        self.create_function(self.another_user, self.target, parentid=self.commentid)
        with pytest.raises(WeasylError) as err:
            self.remove_function(self.commenter, **self.args)
        assert err.value.value == "InsufficientPermissions"

    def test_owner_can_remove(self):
        assert self.target == self.remove_function(self.owner, **self.args)

    def test_mod_can_remove(self):
        assert self.target == self.remove_function(self.moderator, **self.args)

    def test_other_user_can_not_remove(self):
        with pytest.raises(WeasylError) as err:
            self.remove_function(self.another_user, **self.args)
        assert err.value.value == "InsufficientPermissions"


@pytest.mark.usefixtures("db")
class CheckNotificationsTestCase(unittest.TestCase):

    def setUp(self):
        self.owner = db_utils.create_user()
        self.commenter1 = db_utils.create_user()
        self.commenter2 = db_utils.create_user()

    def count_notifications(self, user):
        return (
            d.connect().query(site.SavedNotification)
            .filter(site.SavedNotification.userid == user)
            .count())

    def add_and_remove_comments(self, feature, **kwargs):
        kwargs['content'] = 'hello'

        # commenter1 posts a comment c1 on submission s
        c1 = comment.insert(self.commenter1, parentid=0, **kwargs)
        self.assertEqual(1, self.count_notifications(self.owner))

        # commenter2 posts a reply to c1
        c2 = comment.insert(self.commenter2, parentid=c1, **kwargs)
        self.assertEqual(1, self.count_notifications(self.commenter1))

        # owner posts a reply to c2
        c3 = comment.insert(self.owner, parentid=c2, **kwargs)
        self.assertEqual(1, self.count_notifications(self.commenter2))

        # commenter1 responds to owner
        comment.insert(self.commenter1, parentid=c3, **kwargs)
        self.assertEqual(2, self.count_notifications(self.owner))

        # owner deletes comment thread
        comment.remove(self.owner, feature=feature, commentid=c1)
        self.assertEqual(0, self.count_notifications(self.owner))
        self.assertEqual(0, self.count_notifications(self.commenter1))
        self.assertEqual(0, self.count_notifications(self.commenter2))

    def test_add_and_remove_submission(self):
        s = db_utils.create_submission(self.owner)
        self.add_and_remove_comments('submit', submitid=s)

    def test_add_and_remove_journal(self):
        j = db_utils.create_journal(self.owner)
        self.add_and_remove_comments('journal', journalid=j)

    def test_add_and_remove_character(self):
        c = db_utils.create_character(self.owner)
        self.add_and_remove_comments('char', charid=c)

    def test_add_and_remove_shout(self):
        # commenter1 posts a shout on owner's page
        c1 = shout.insert(self.commenter1, target_user=self.owner, parentid=0, content="hello", staffnotes=False)
        self.assertEqual(1, self.count_notifications(self.owner))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 1)
        self.assertTrue(shouts[0].items() >= {"content": "hello"}.items())

        # commenter2 posts a reply to c1
        c2 = shout.insert(self.commenter2, target_user=self.owner, parentid=c1, content="reply", staffnotes=False)
        self.assertEqual(1, self.count_notifications(self.commenter1))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 2)
        self.assertTrue(shouts[1].items() >= {"content": "reply"}.items())

        # owner posts a reply to c2
        c3 = shout.insert(self.owner, target_user=self.owner, parentid=c2, content="reply 2", staffnotes=False)
        self.assertEqual(1, self.count_notifications(self.commenter2))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 3)
        self.assertTrue(shouts[2].items() >= {"content": "reply 2"}.items())

        # commenter1 responds to owner
        shout.insert(self.commenter1, target_user=self.owner, parentid=c3, content="reply 3", staffnotes=False)
        self.assertEqual(2, self.count_notifications(self.owner))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 4)
        self.assertTrue(shouts[3].items() >= {"content": "reply 3"}.items())

        # commenter1 posts a new root shout
        shout.insert(self.commenter1, target_user=self.owner, parentid=0, content="root 2", staffnotes=False)
        self.assertEqual(3, self.count_notifications(self.owner))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 5)
        self.assertTrue(shouts[0].items() >= {"content": "root 2"}.items())
        self.assertTrue(shouts[4].items() >= {"content": "reply 3"}.items())

        # commenter2 posts another reply to c1
        shout.insert(self.commenter2, target_user=self.owner, parentid=c1, content="reply 4", staffnotes=False)
        self.assertEqual(2, self.count_notifications(self.commenter1))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 6)
        self.assertTrue(shouts[5].items() >= {"content": "reply 4"}.items())

        # owner deletes comment thread
        shout.remove(self.owner, commentid=c1)
        self.assertEqual(1, self.count_notifications(self.owner))
        self.assertEqual(0, self.count_notifications(self.commenter1))
        self.assertEqual(0, self.count_notifications(self.commenter2))

        shouts = shout.select(0, self.owner)
        self.assertEqual(len(shouts), 1)
        self.assertTrue(shouts[0].items() >= {"content": "root 2"}.items())

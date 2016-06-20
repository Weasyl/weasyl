
import unittest
import pytest
import mock

import db_utils

from weasyl import profile, followuser, orm, define as d
from weasyl.error import WeasylError


@pytest.mark.usefixtures('db')
class FollowUserTestCase(unittest.TestCase):

    @mock.patch("weasyl.define.get_config")
    @mock.patch("weasyl.welcome.followuser_remove")
    @mock.patch("weasyl.welcome.followuser_insert")
    def test_insert(self, followuser_insert, followuser_remove, get_config):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        get_config.side_effect = lambda userid: "scftj"

        self.assertFalse(profile.select_relation(user1, user2)["follow"])
        # user1 watches user2
        followuser.insert(user1, user2)
        self.assertEqual(1, d.sessionmaker().query(orm.Follow).count())
        # profile.select_relation should return u1 follows u2, u2 is follower of u1, u1 is not
        # follower of u2
        self.assertTrue(profile.select_relation(user1, user2)["follow"])
        self.assertTrue(profile.select_relation(user2, user1)["follower"])
        self.assertFalse(profile.select_relation(user1, user2)["follower"])
        followuser_remove.assert_called_once_with(user1, user2)
        followuser_insert.assert_called_once_with(user1, user2)
        self.assertEqual("cfjst", d.sessionmaker().query(orm.Follow).first().settings)

    @mock.patch("weasyl.define.get_config")
    @mock.patch("weasyl.welcome.followuser_remove")
    @mock.patch("weasyl.welcome.followuser_insert")
    def test_insert_s_only(self, followuser_insert, followuser_remove, get_config):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()
        get_config.side_effect = lambda userid: "s"

        # user1 watches user2
        followuser.insert(user1, user2)
        self.assertTrue(profile.select_relation(user1, user2)["follow"])
        self.assertTrue(profile.select_relation(user2, user1)["follower"])
        self.assertEqual(1, d.sessionmaker().query(orm.Follow).count())
        followuser_remove.assert_called_once_with(user1, user2)
        followuser_insert.assert_called_once_with(user1, user2)
        self.assertEqual("s", d.sessionmaker().query(orm.Follow).first().settings)

    def test_insert_ignores(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()

        # user1 ignores user2
        db_utils.create_ignoreuser(user1, user2)
        # attempts to follow in either direction throw a WeasylError
        self.assertRaises(WeasylError, followuser.insert, user1, user2)
        self.assertRaises(WeasylError, followuser.insert, user2, user1)
        self.assertFalse(profile.select_relation(user1, user2)["follow"])
        self.assertFalse(profile.select_relation(user2, user1)["follower"])

    def test_update(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()

        # user1 watches user2
        followuser.insert(user1, user2)

        # user1 updates watch settings
        followuser.update(user1, user2, followuser.WatchSettings.from_code("cf"))
        self.assertEqual("cf", d.sessionmaker().query(orm.Follow).first().settings)

        # again
        followuser.update(user1, user2, followuser.WatchSettings.from_code("st"))
        self.assertTrue(profile.select_relation(user1, user2)["follow"])
        self.assertTrue(profile.select_relation(user2, user1)["follower"])
        self.assertEqual("st", d.sessionmaker().query(orm.Follow).first().settings)

    @mock.patch("weasyl.welcome.followuser_remove")
    def test_remove(self, followuser_remove):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()

        # user1 watches user2
        followuser.insert(user1, user2)
        self.assertEqual(1, d.sessionmaker().query(orm.Follow).count())

        followuser_remove.reset_mock()

        # user1 changed their mind
        followuser.remove(user1, user2)
        self.assertFalse(profile.select_relation(user1, user2)["follow"])
        self.assertFalse(profile.select_relation(user2, user1)["follower"])
        self.assertEqual(0, d.sessionmaker().query(orm.Follow).count())
        followuser_remove.assert_called_once_with(user1, user2)

    def test_mutual_follow(self):
        user1 = db_utils.create_user()
        user2 = db_utils.create_user()

        # user1 watches user2
        followuser.insert(user1, user2)
        # user2 watches user1
        followuser.insert(user2, user1)
        self.assertTrue(profile.select_relation(user1, user2)["follow"])
        self.assertTrue(profile.select_relation(user2, user1)["follower"])
        self.assertTrue(profile.select_relation(user2, user1)["follow"])
        self.assertTrue(profile.select_relation(user1, user2)["follower"])

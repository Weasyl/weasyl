import unittest
import pytest

from weasyl.test import db_utils

from weasyl import define as d
from weasyl import profile


@pytest.mark.usefixtures('db')
class ProfileManageTestCase(unittest.TestCase):

    def setUp(self):
        self.mod = db_utils.create_user()
        self.user = db_utils.create_user()

        links = [
            {
                'userid': self.user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': self.user,
                'link_type': 'Email',
                'link_value': 'mailto:support@weasyl.com',
            },
        ]

        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

    def test_select_manage(self):
        test_user_profile = profile.select_manage(self.user)

        self.assertEqual(len(test_user_profile['user_links']), 2)

    def test_remove_social_links(self):
        profile.do_manage(self.mod, self.user, remove_social=['Email'])

        test_user_profile = profile.select_manage(self.user)

        self.assertEqual(len(test_user_profile['user_links']), 1)
        self.assertEqual(test_user_profile['user_links'][0][1][0], 'Weasyl')

import unittest
import pytest

from weasyl.test import db_utils

from weasyl import define as d
from weasyl import profile


@pytest.mark.usefixtures('db')
class ProfileManageTestCase(unittest.TestCase):

    def setUp(self):
        self.mod = db_utils.create_user()

    def test_select_manage(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:support@weasyl.com',
            },
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        test_user_profile = profile.select_manage(user)
        self.assertEqual(len(test_user_profile['sorted_user_links']), 2)

    def test_remove_social_links(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:support@weasyl.com',
            },
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        profile.do_manage(self.mod, user, remove_social=['Email'])

        test_user_profile = profile.select_manage(user)
        self.assertEqual(test_user_profile['sorted_user_links'], [('Twitter', ['Weasyl'])])

    def test_sort_user_links(self):
        user = db_utils.create_user()

        links = [
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'Weasyl',
            },
            {
                'userid': user,
                'link_type': 'Email',
                'link_value': 'mailto:sysop@weasyl.com',
            },
            {
                'userid': user,
                'link_type': 'Twitter',
                'link_value': 'WeasylDev',
            }
        ]
        d.engine.execute(d.meta.tables['user_links'].insert().values(links))

        test_user_profile = profile.select_manage(user)
        self.assertEqual(test_user_profile['sorted_user_links'], [
            ('Email', ['mailto:sysop@weasyl.com']),
            ('Twitter', ['Weasyl', 'WeasylDev']),
        ])

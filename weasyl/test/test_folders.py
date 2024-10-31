import unittest
import pytest

from libweasyl import ratings

from weasyl import folder
from weasyl.test import db_utils

# configurations for folders:
#   hidden
#   no-notifications
#   profile-filter
#   index-filter
#   featured-filter


@pytest.mark.usefixtures('db')
class FolderTestCase(unittest.TestCase):
    def setUp(self):
        user1 = db_utils.create_user()
        self.folder_object = db_utils.create_folder(user1)
        self.submission = db_utils.create_submission(
            user1, ratings.GENERAL.code, folderid=self.folder_object)

    def test_settings_start_false(self):
        self.assertFalse(folder.submission_has_folder_flag(self.submission, 'f'))  # featured-filter
        self.assertFalse(folder.submission_has_folder_flag(self.submission, 'm'))  # index-filter
        self.assertFalse(folder.submission_has_folder_flag(self.submission, 'u'))  # profile-filter
        self.assertFalse(folder.submission_has_folder_flag(self.submission, 'n'))  # no-notifications

    def test_setting_f(self):
        folder.update_settings(self.folder_object, 'f')
        self.assertTrue(folder.submission_has_folder_flag(self.submission, 'f'))  # featured-filter

    def test_setting_m(self):
        folder.update_settings(self.folder_object, 'm')
        self.assertTrue(folder.submission_has_folder_flag(self.submission, 'm'))  # index-filter

    def test_setting_u(self):
        folder.update_settings(self.folder_object, 'u')
        self.assertTrue(folder.submission_has_folder_flag(self.submission, 'u'))  # profile-filter

    def test_setting_n(self):
        folder.update_settings(self.folder_object, 'n')
        self.assertTrue(folder.submission_has_folder_flag(self.submission, 'n'))  # no-notifications

from __future__ import absolute_import

import unittest
import pytest

from weasyl import api
from weasyl.test import db_utils


@pytest.mark.usefixtures('db')
class ApiTestCase(unittest.TestCase):
    def test_get_api_keys(self):
        user = db_utils.create_user()
        self.assertEqual(0, api.get_api_keys(user).rowcount)
        token = "some token"
        db_utils.create_api_key(user, token)
        self.assertEqual(1, api.get_api_keys(user).rowcount)
        self.assertEqual(token, api.get_api_keys(user).first()["token"])

    def test_add_api_key(self):
        user = db_utils.create_user()
        api.add_api_key(user, "")
        self.assertEqual(1, api.get_api_keys(user).rowcount)

    def test_delete_api_keys(self):
        user = db_utils.create_user()
        token = "some token"
        db_utils.create_api_key(user, token)
        api.delete_api_keys(user, [token])
        self.assertEqual(0, api.get_api_keys(user).rowcount)

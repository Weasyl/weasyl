import unittest
from libweasyl import security


class SecurityTestCase(unittest.TestCase):
    def test_generate_key(self):
        length = 20
        self.assertEqual(length, len(security.generate_key(length)))

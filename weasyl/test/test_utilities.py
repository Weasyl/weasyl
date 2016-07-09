import unittest

from weasyl import login


class PasswordChecksTestCase(unittest.TestCase):
    def testPasswordLength(self):
        # Too short
        self.assertFalse(login.password_secure(u""))
        self.assertFalse(login.password_secure(u"Abc123*"))
        self.assertFalse(login.password_secure(u"Passw0rd"))

        # Acceptable
        self.assertTrue(login.password_secure(u"abcdefghijkl"))

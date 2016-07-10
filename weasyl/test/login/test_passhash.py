"""
Test suite for function: login.py::def passhash(password):
"""
import bcrypt

from weasyl import login


# Main test password
raw_password = "0123456789"


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)


def test_passhash():
    # Generate a bcrypt hash from .passhash
    bcrypt_hash = login.passhash(raw_password)
    assert bcrypt_hash
    # Verify the password hashes correctly.
    assert bcrypt.checkpw(raw_password.encode('utf-8'), bcrypt_hash.encode('utf-8'))

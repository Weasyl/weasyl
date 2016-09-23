from __future__ import absolute_import

from weasyl import login


def test_password_secure():
    # Too short
    assert not login.password_secure(u"")
    assert not login.password_secure(u"Abc123*")
    assert not login.password_secure(u"Passw0rd")

    # Acceptable
    assert login.password_secure(u"abcdefghijkl")

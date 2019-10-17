

from weasyl import login


def test_password_secure():
    # Too short
    assert not login.password_secure("")
    assert not login.password_secure("Abc123*")
    assert not login.password_secure("Passw0rd")

    # Acceptable
    assert login.password_secure("abcdefghijkl")

"""
Test suite for function: login.py::def password_secure(password):
"""
from weasyl import login


def test_password_secure():
    # Length too short (len < login._PASSWORD)
    test_string = ""
    for i in range(0, login._PASSWORD):
        assert not login.password_secure(test_string)
        test_string = test_string + 'a'

    # Acceptable length (len >= login._PASSWORD)
    for i in range(login._PASSWORD, login._PASSWORD + 3):
        test_string = test_string + 'a'
        assert login.password_secure(test_string)

    # Run secondary tests; the following three assertions are not long enough passwords (len < login._PASSWORD)
    assert not login.password_secure(u"")
    assert not login.password_secure(u"Abc123*")
    assert not login.password_secure(u"Passw0rd")

    # This assertion is an acceptable length of password (len >= login._PASSWORD)
    assert login.password_secure(u"abcdefghij")
    assert login.password_secure(u"abcdefghijk")
    assert login.password_secure(u"abcdefghijkl")

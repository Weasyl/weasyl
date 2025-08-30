import pytest

from weasyl.users import USERNAME_MAX_LENGTH
from weasyl.users import Username
from weasyl.users import UsernameTooLong


def test_username():
    assert Username.create("  🛇  te  🛇  st  🛇  ") == Username(display="te st", sysname="test"), "whitespace should be normalized"
    assert Username.create("ź") == Username(display="z", sysname="z"), "non-ASCII characters should get ASCII equivalents when possible"


def test_username_lengths():
    assert Username.create("a") == Username(display="a", sysname="a")

    mlu = "a" * USERNAME_MAX_LENGTH
    assert Username.create(mlu) == Username(display=mlu, sysname=mlu)

    with pytest.raises(UsernameTooLong):
        Username.create(mlu + "a")

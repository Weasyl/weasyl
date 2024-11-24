from weasyl.users import Username


def test_username():
    assert Username.create("  🛇  te  🛇  st  🛇  ") == Username(display="te st", sysname="test"), "whitespace should be normalized"
    assert Username.create("ź") == Username(display="z", sysname="z")

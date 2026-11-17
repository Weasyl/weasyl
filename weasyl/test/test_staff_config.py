import pytest

from libweasyl.staff import StaffConfig
from weasyl import macro
from weasyl import staff_config


@pytest.mark.parametrize(
    'content,exception',
    (
        ('directors = [2000]; import sys', SyntaxError),
        ('directors, wesley = [1, 2]', SyntaxError),
        ('foo = True', SyntaxError),
        ('directors = "2000"', SyntaxError),
        ('directors = b"2000"', SyntaxError),
        ('directors = [0]', SyntaxError),
        ('directors = [2000]; directors = [2001]', SyntaxError),
        ('wesley = [2000]', SyntaxError),
        ('wesley = eval("evil")', ValueError),
    ),
)
def test_bad_configuration(monkeypatch, tmp_path, content, exception):
    bad_config = tmp_path / 'bad-config.py'
    bad_config.write_text(content)
    monkeypatch.setattr(macro, 'MACRO_SYS_STAFF_CONFIG_PATH', str(bad_config))

    with pytest.raises(exception):
        staff_config.load()


def test_good_configuration(monkeypatch, tmp_path):
    good_config = tmp_path / 'good-config.py'
    good_config.write_text("""\
directors = [2000]
admins = [2001, 2002]
mods = [2003, 2004, 2005]
developers = [1, 2147483647]
wesley = 2008
""")
    monkeypatch.setattr(macro, 'MACRO_SYS_STAFF_CONFIG_PATH', str(good_config))

    assert staff_config.load() == StaffConfig(
        directors=[2000],
        admins=[2001, 2002],
        mods=[2003, 2004, 2005],
        developers=[1, 2147483647],
        wesley=2008,
    )

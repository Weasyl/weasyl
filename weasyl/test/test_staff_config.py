import pytest

from weasyl import macro
from weasyl import staff_config


@pytest.mark.parametrize(
    'content,exception',
    (
        ('directors = [2000]; import sys', SyntaxError),
        ('directors, wesley = [1, 2]', SyntaxError),
        ('foo = True', SyntaxError),
        ('wesley = eval("evil")', ValueError),
    ),
)
def test_bad_configuration(monkeypatch, tmp_path, content, exception):
    bad_config = tmp_path / 'bad-config.py'
    bad_config.write_text(content)
    monkeypatch.setattr(macro, 'MACRO_SYS_STAFF_CONFIG_PATH', str(bad_config))

    with pytest.raises(exception):
        staff_config.load()


def test_ignore_technical_staff(monkeypatch, tmp_path):
    config = tmp_path / 'config.py'
    config.write_text('directors = [1]; technical_staff = [2]; wesley = 3')
    monkeypatch.setattr(macro, 'MACRO_SYS_STAFF_CONFIG_PATH', str(config))

    staff = staff_config.load()

    assert staff['directors'] == [1]
    assert 'technical_staff' not in staff
    assert staff['wesley'] == 3

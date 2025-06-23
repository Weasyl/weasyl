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

import pytest

from weasyl import forms
from weasyl.error import WeasylError


INVALID_IDS = (
    '',
    'a',
    '0',
    '-1',
    '9999999999999999999999',
    '\0',
    '٨',
)

VALID_IDS = (
    ('1', 1),
    ('2147483647', 2147483647),
)


@pytest.mark.parametrize('string', INVALID_IDS)
def test_expect_id_invalid(string: str):
    with pytest.raises(WeasylError):
        forms.expect_id(string)


@pytest.mark.parametrize('string,expected', VALID_IDS)
def test_expect_id_valid(string: str, expected: int):
    assert forms.expect_id(string) == expected

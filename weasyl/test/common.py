import pytest

from weasyl.error import WeasylError


def raises_app_error(code: str):
    return pytest.raises(WeasylError, check=lambda err: err.value == code)

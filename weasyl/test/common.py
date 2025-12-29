import pytest

from libweasyl.test.common import autocommit_cursor
from weasyl.error import WeasylError
from weasyl.rate_limits import RateLimitId


def raises_app_error(code: str):
    return pytest.raises(WeasylError, check=lambda err: err.value == code)


def initialize_database(engine):
    with autocommit_cursor(engine) as cur:
        cur.execute("INSERT INTO global_rate_limits (id) VALUES (%s)", (RateLimitId.MAIL_OUT.value,))

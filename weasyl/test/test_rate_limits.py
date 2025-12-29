import time

import weasyl.define as d
from weasyl.rate_limits import GlobalRateLimit
from weasyl.rate_limits import RateLimitId
from weasyl.test.common import raises_app_error


def test_rate_limits(db) -> None:
    start_time = time.monotonic()

    rate_limit = GlobalRateLimit.parse(RateLimitId.MAIL_OUT, "5/60")

    # use up capacity
    for _ in range(5):
        rate_limit.take_one()

    # at capacity
    with raises_app_error("globalLimit"):
        rate_limit.take_one()

    # Simulate time passing. One unit of new capacity in 60/5 = 12 ticks, but the test might have started just before a tick.
    d.engine.execute("UPDATE global_rate_limits SET last_update = last_update - 10 WHERE id = %(id)s", id=rate_limit.id.value)

    # still at capacity
    with raises_app_error("globalLimit"):
        rate_limit.take_one()

    # one unit of new capacity
    d.engine.execute("UPDATE global_rate_limits SET last_update = last_update - 2 WHERE id = %(id)s", id=rate_limit.id.value)
    rate_limit.take_one()
    assert time.monotonic() - start_time < 0.5  # ensure time-based test isn't invalidated by unexpected latency

    # at capacity again
    with raises_app_error("globalLimit"):
        rate_limit.take_one()

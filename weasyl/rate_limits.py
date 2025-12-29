from __future__ import annotations

import enum
from dataclasses import dataclass

from weasyl import define as d
from weasyl.error import WeasylError


@enum.unique
class RateLimitId(enum.Enum):
    MAIL_OUT = "mail-out"


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class GlobalRateLimit:
    """
    A database-backed token-bucket-style rate limit that fills up to `capacity` at the rate of `capacity`/`period` with second granularity.

    Enforces (clock adjustments and event latency aside) that no time span of `period` ever contains more than `2 * capacity` events, and that the average rate of events converges to at most `capacity`/`period`.
    """

    id: RateLimitId

    capacity: int

    period: int
    """The period for `capacity`, in seconds."""

    def __post_init__(self) -> None:
        # Overflow considerations:
        # - `ticks * capacity` must fit in SQL `bigint`, where `ticks` is the number of seconds between rate limit triggers, but is the number of seconds since the Unix epoch on the first trigger
        # - `capacity + ticks * capacity / period` must fit in SQL `bigint`
        # - `capacity` must fit in SQL `integer`
        # - `period` must fit in SQL `bigint`
        # Upper bounds here are semi-arbitrary values big enough in practice and satisfying the preceding requirements on PostgreSQL.
        if not 0 <= self.capacity <= 0x3fff_ffff:
            raise ValueError("rate limit capacity out of range")
        if not 0 < self.period <= 0x3fff_ffff:
            raise ValueError("rate limit period out of range")

    def take_one(self) -> None:
        TICKS = "greatest(0, trunc(EXTRACT(EPOCH FROM now()))::int8 - last_update)"
        NEWLY_AVAILABLE = f"({TICKS} * %(capacity)s / %(period)s)"
        result = d.engine.execute(
            "UPDATE global_rate_limits"
            f" SET available = least(%(capacity)s, available + {NEWLY_AVAILABLE}) - 1,"
            f" last_update = last_update + {TICKS}"
            " WHERE id = %(id)s"
            f" AND (available > 0 OR {NEWLY_AVAILABLE} > 0)",
            capacity=self.capacity,
            period=self.period,
            id=self.id.value,
        )

        if result.rowcount == 0:
            raise WeasylError("globalLimit", level="error")

        assert result.rowcount == 1

    @classmethod
    def parse(cls, id: RateLimitId, expr: str) -> GlobalRateLimit:
        capacity, period = map(int, expr.split("/"))
        return cls(
            id=id,
            capacity=capacity,
            period=period,
        )

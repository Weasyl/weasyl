"""
Support for legacy code.

*DO NOT* use things from this module if it can be avoided at all. That is not
to say that the functionality should be duplicated, but that things in this
module are supporting old, crufty code, and newly-written code should not need
to use them.
"""

import datetime
from collections.abc import Callable
from typing import NoReturn
from typing import TypeVar
from typing import overload

import sqlalchemy as sa
from psycopg2.errors import DatatypeMismatch
from sqlalchemy import func


UNIXTIME_OFFSET = -18000
"""
The offset added to UNIX timestamps before storing them in the database.
"""


UNIXTIME_NOW_SQL = func.extract('epoch', func.now()).cast(sa.BigInteger()) + sa.bindparam('offset', UNIXTIME_OFFSET, literal_execute=True)


def get_offset_unixtime(dt: datetime.datetime) -> int:
    if dt.tzinfo is None:
        raise ValueError("datetime must be time-zone-aware")

    return int(dt.timestamp()) + UNIXTIME_OFFSET


T = TypeVar("T")


@overload
def birthdate_retry(action: Callable[[int | datetime.date], T], value: datetime.date) -> T:
    ...


@overload
def birthdate_retry(action: Callable[[int | datetime.date | None], T], value: datetime.date | None) -> T:
    ...


def birthdate_retry(action, value):
    """
    Try an action with an `int` offset-unixtime value first, where that `int` might be used in one or more SQL queries where a `date` is expected, then re-run the action with a `date` if the action fails due to an SQL data type error.

    For use as part of a migration that updates the type of the `birthday` column in-place.

    The old schema is tried first, since the migration could happen between the first attempt and the fallback.
    """
    if value is None:
        return action(None)

    # midnight at the given date
    dt = datetime.datetime.combine(value, datetime.time.min, tzinfo=datetime.timezone.utc)
    offset_unixtime = get_offset_unixtime(dt)

    try:
        return action(offset_unixtime)
    except sa.exc.ProgrammingError as e:
        if not isinstance(e.orig, DatatypeMismatch):
            raise

        return action(value)


MaybeNone = TypeVar("MaybeNone", None, NoReturn)


def birthdate_adapt(value: int | datetime.date | MaybeNone) -> datetime.date | MaybeNone:
    """
    Convert a value that might have originated from either an offset-unixtime SQL `integer` or an SQL `date` to a `date`.

    For use as part of a migration that updates the type of the `birthday` column in-place.
    """
    if value is None or isinstance(value, datetime.date):
        return value

    return datetime.datetime.fromtimestamp(value - UNIXTIME_OFFSET, datetime.timezone.utc).date()

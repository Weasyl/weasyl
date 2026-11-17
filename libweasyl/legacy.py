"""
Support for legacy code.

*DO NOT* use things from this module if it can be avoided at all. That is not
to say that the functionality should be duplicated, but that things in this
module are supporting old, crufty code, and newly-written code should not need
to use them.
"""

import datetime

import sqlalchemy as sa
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

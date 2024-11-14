from typing import Iterable, TypeVar

from weasyl.error import WeasylError


_T = TypeVar("T")


def expect_id(s: str) -> int:
    """
    Parse the default (`%d`-like) string representation of a PostgreSQL generated `integer` identity column to an `int`, throwing if it doesn't match this format.

    `expect_id(a) == expect_id(b)` implies `a == b`.
    """
    if (
        1 <= len(s) <= 10  # len(str(2**31-1))
        and (bs := s.encode()).isdigit()
        and not bs.startswith(b"0")
    ):
        return int(bs)

    raise WeasylError("Unexpected")


def only(iterable: Iterable[_T]) -> _T:
    try:
        x = next(iterable)
    except StopIteration:
        pass
    else:
        try:
            next(iterable)
        except StopIteration:
            return x

    raise WeasylError("Unexpected")

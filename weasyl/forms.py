from typing import Iterable, TypeVar

from weasyl.error import WeasylError


T = TypeVar("T")


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


def expect_ids(values: Iterable[str]) -> list[int]:
    return list(map(expect_id, values))


def only(iterable: Iterable[T]) -> T:
    iterator = iter(iterable)

    try:
        x = next(iterator)
    except StopIteration:
        pass
    else:
        try:
            next(iterator)
        except StopIteration:
            return x

    raise WeasylError("Unexpected")

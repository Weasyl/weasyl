from typing import Iterable, TypeVar

from weasyl.error import WeasylError


_T = TypeVar("T")


def expect_id(s: str) -> int:
    if (
        1 <= len(s) <= 10  # len(str(2**31-1))
        and (bs := s.encode()).isdigit()
        and (id_ := int(bs)) > 0
    ):
        return id_

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

from typing import Iterable, TypeVar
from urllib.parse import urlsplit

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


def checked_redirect(path: str) -> str:
    """
    Returns the passed URL, asserting that it’s a valid place to redirect back to within the same application (e.g. after logging in).
    """
    split_result = urlsplit(path)

    if split_result.scheme or split_result.netloc:
        raise WeasylError("Unexpected", level="warning")

    return path

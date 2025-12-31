import re
import unicodedata
from typing import Iterable, NewType, TypeVar

from libweasyl.constants import TAG_MAX_LENGTH
from weasyl.error import WeasylError
from weasyl.users import USERNAME_MAX_LENGTH


_NON_SYSNAME = re.compile(r"[^0-9a-z]")
_NORMALIZED_TAG = re.compile(r"[0-9a-z]+(?:_[0-9a-z]+)*")


T = TypeVar("T")


def expect_id(s: str) -> int:
    """
    Parse the default (`%d`-like) string representation of a PostgreSQL generated `integer` identity column to an `int`, throwing if it doesn't match this format and range.

    `expect_id(a) == expect_id(b)` implies `a == b`.
    """
    if (
        1 <= len(s) <= 10  # len(str(2**31 - 1))
        and (bs := s.encode()).isdigit()
        and not bs.startswith(b"0")
        and (n := int(bs)) <= 2**31 - 1
    ):
        return n

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


def parse_sysname(s: str) -> str | None:
    """
    Attempt to convert a string to a sysname suitable for exact lookup against the `login.login_name` column, returning `None` if the result is not usable as a sysname filter.

    Note: This never returns `None` for valid sysnames, but it doesn’t always return `None` for invalid sysnames, e.g. the prohibited ones in `weasyl.users._BANNED_SYSNAMES`.

    `Username.create(s).sysname == parse_sysname(s)` when the LHS doesn’t throw.
    """
    normalized = unicodedata.normalize("NFKD", s.lower())
    sysname = _NON_SYSNAME.sub("", normalized)

    return sysname if 0 < len(sysname) <= USERNAME_MAX_LENGTH else None


def parse_sysname_list(s: str) -> list[str]:
    """
    Parse a list of sysnames (in the sense of `parse_sysname`) from a string of semicolon-delimited usernames, leaving out entries that aren’t well-formed usernames.
    """
    return list(filter(None, map(parse_sysname, s.split(";"))))


NormalizedTag = NewType("NormalizedTag", str)


def parse_tag(target: str) -> NormalizedTag | None:
    target = "".join(i for i in target if ord(i) < 128)
    target = target.replace(" ", "_")
    target = "".join(i for i in target if i.isalnum() or i in "_")
    target = target.strip("_")
    target = "_".join(i for i in target.split("_") if i)

    if len(target) > TAG_MAX_LENGTH:
        raise WeasylError("tagTooLong")

    return NormalizedTag(target.lower()) if target else None


def expect_tag(s: str) -> NormalizedTag:
    if not (0 < len(s) <= TAG_MAX_LENGTH and _NORMALIZED_TAG.fullmatch(s)):
        raise WeasylError("Unexpected")

    return NormalizedTag(s)

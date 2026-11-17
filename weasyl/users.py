from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from weasyl.error import WeasylError


USERNAME_MAX_LENGTH = 25

_NON_SYSNAME = re.compile(r"[^0-9a-z]")
_NON_USERNAME_WORD = re.compile(r"[^!-~]|;")

_BANNED_SYSNAMES = frozenset({
    "admin",
    "administrator",
    "mod",
    "moderator",
    "weasyl",
    "weasyladmin",
    "weasylmod",
    "staff",
    "security",
})


class UsernameInvalid(WeasylError):
    value = "usernameInvalid"


class UsernameTooLong(UsernameInvalid):
    level = "warning"  # client-side `maxlength` makes this logworthy


class UsernameBanned(UsernameInvalid):
    value = "usernameBanned"


def _get_sysname_unchecked(s: str) -> str:
    return _NON_SYSNAME.sub("", s.lower())


@dataclass(order=False, frozen=True, slots=True)
class Username:
    """
    A Weasyl username is a string of printable ASCII – including the space character, but not including the semicolon – containing at least one alphanumeric, and at most `USERNAME_MAX_LENGTH` characters long, with no leading, trailing, or multiple consecutive space.

    Username equivalence is case-insensitive and considers only alphanumerics. In other words, it’s determined by equality of the “sysname”, which is the URL-safe canonical identifier derived from the display username by stripping non-alphanumerics and converting to lowercase.
    """
    display: str
    sysname: str

    # TODO: Python 3.11+: `-> Self`
    @classmethod
    def from_stored(cls, stored: str) -> Username:
        """
        Create from a known-valid username stored in the `profile.username` column.
        """
        sysname = _get_sysname_unchecked(stored)

        if (
            not sysname
            or len(stored) > USERNAME_MAX_LENGTH
            or not stored.isascii()
            or not stored.isprintable()
            or ";" in stored
        ):
            # reaching this indicates incorrect use of the function; don’t rely on this behavior
            raise ValueError("invalid username")  # pragma: no cover

        return cls(
            display=stored,
            sysname=sysname,
        )

    @classmethod
    def create(cls, text: str) -> Username:
        """
        Parse a request for a new username, like when creating an account or changing usernames.

        To parse a lookup for an existing username, use `weasyl.forms.parse_sysname`.
        """
        words = unicodedata.normalize("NFKD", text).split()
        cleaned_words = (_NON_USERNAME_WORD.sub("", word) for word in words)
        cleaned = " ".join(filter(None, cleaned_words))

        if len(cleaned) > USERNAME_MAX_LENGTH:
            raise UsernameTooLong()

        sysname = _get_sysname_unchecked(cleaned)

        if not sysname:
            raise UsernameInvalid()

        if sysname in _BANNED_SYSNAMES:
            raise UsernameBanned()

        return cls(
            display=cleaned,
            sysname=sysname,
        )

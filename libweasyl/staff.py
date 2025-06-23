"""
Sets of Weasyl staff user ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


DIRECTORS: frozenset[int] = frozenset()
""" Directors have the same powers as admins. """

ADMINS: frozenset[int] = frozenset()
""" Site administrators can update site news and moderate user content. """

MODS: frozenset[int] = frozenset()
""" Site moderators can hide submissions, manage non-admin users, etc. """

DEVELOPERS: frozenset[int] = frozenset()
""" Purely cosmetic group for users who contribute to site development. """

WESLEY: int | None = None
""" The site mascot. Option for the owner of a site update. """


@dataclass(frozen=True, slots=True)
class StaffConfig:
    directors: Iterable[int] = ()
    admins: Iterable[int] = ()
    mods: Iterable[int] = ()
    developers: Iterable[int] = ()
    wesley: int | None = None


def _init_staff(config: StaffConfig) -> None:
    """
    Populate staff members.
    """
    global DIRECTORS
    DIRECTORS = frozenset(config.directors)

    global ADMINS
    ADMINS = DIRECTORS | frozenset(config.admins)

    global MODS
    MODS = ADMINS | frozenset(config.mods)

    global DEVELOPERS
    DEVELOPERS = frozenset(config.developers)

    global WESLEY
    WESLEY = config.wesley

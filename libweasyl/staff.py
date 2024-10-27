"""
Sets of Weasyl staff user ids.
"""

from collections.abc import Iterable

DIRECTORS = frozenset()
""" Directors have the same powers as admins. """

TECHNICAL = frozenset()
""" Technical staff can moderate all content and manage all users. """

ADMINS = frozenset()
""" Site administrators can update site news and moderate user content. """

MODS = frozenset()
""" Site moderators can hide submissions, manage non-admin users, etc. """

DEVELOPERS = frozenset()
""" Purely cosmetic group for users who contribute to site development. """

WESLEY = None
""" The site mascot. Option for the owner of a site update. """


def _init_staff(directors: Iterable[int] = (), technical_staff: Iterable[int] = (),
                admins: Iterable[int] = (), mods: Iterable[int] = (),
                developers: Iterable[int] = (), wesley: int | None = None):
    """
    Populates staff members from passed kwargs.

    Parameters:
        directors: Array with directors
        technical_staff: Array with technical staff
        admins: array with admins
        mods: Array with mods
        developers: Array with developers
    """
    global DIRECTORS
    DIRECTORS = frozenset(directors)

    global TECHNICAL
    TECHNICAL = DIRECTORS | frozenset(technical_staff)

    global ADMINS
    ADMINS = TECHNICAL | frozenset(admins)

    global MODS
    MODS = ADMINS | frozenset(mods)

    global DEVELOPERS
    DEVELOPERS = frozenset(developers)

    global WESLEY
    WESLEY = wesley

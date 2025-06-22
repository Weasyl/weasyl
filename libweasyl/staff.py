"""
Sets of Weasyl staff user ids.
"""

DIRECTORS = frozenset()
""" Directors have the same powers as admins. """

ADMINS = frozenset()
""" Site administrators can update site news and moderate user content. """

MODS = frozenset()
""" Site moderators can hide submissions, manage non-admin users, etc. """

DEVELOPERS = frozenset()
""" Purely cosmetic group for users who contribute to site development. """

WESLEY = None
""" The site mascot. Option for the owner of a site update. """


def _init_staff(directors=(), admins=(), mods=(), developers=(), wesley=None):
    """
    Populates staff members from passed kwargs.

    Parameters:
        directors: Array with directors
        admins: array with admins
        mods: Array with mods
        developers: Array with developers
    """
    global DIRECTORS
    DIRECTORS = frozenset(directors)

    global ADMINS
    ADMINS = DIRECTORS | frozenset(admins)

    global MODS
    MODS = ADMINS | frozenset(mods)

    global DEVELOPERS
    DEVELOPERS = frozenset(developers)

    global WESLEY
    WESLEY = wesley

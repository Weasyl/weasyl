"""
Sets of Weasyl staff user ids.
"""

def _init_staff(directors, technical_staff, admins, mods, developers):
    """
    Populates staff members from passed kwargs.

    Parameters:
        directors: Array with directors
        technical_staff: Array with technical staff
        admins: array with admins
        mods: Array with mods
        developers: Array with developers
    """

    """ Directors have the same powers as admins. """
    global DIRECTORS
    DIRECTORS = frozenset(directors)

    """ Technical staff can moderate all content and manage all users. """
    global TECHNICAL
    TECHNICAL = DIRECTORS | frozenset(technical_staff)

    """ Site administrators can update site news and moderate user content. """
    global ADMINS
    ADMINS = TECHNICAL | frozenset(admins)

    """ Site moderators can hide submissions, manage non-admin users, etc. """
    global MODS
    MODS = ADMINS | frozenset(mods)

    """ Purely cosmetic group for users who contribute to site development. """
    global DEVELOPERS
    DEVELOPERS = frozenset(developers)

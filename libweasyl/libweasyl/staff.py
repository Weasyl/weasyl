"""
Dictionaries of Weasyl staff.

This module must be initialized with a call to `staff._init_staff(staffDict)`
where ``staffDict`` is a nested dictionary of staff members identified by their
user ID. An example of such a call might look as follows (comments optional):

MACRO_SYS_STAFF_CONFIG = {
    #[Fiz, Ikani]
    'directors': [1014, 2061],
    #[Weykent]
    'technical_staff': [5756],
    #[Hendikins, Kihari]
    'admins': [23613, 3],
    #[pinardilla]
    'mods': [40212],
    #[8BitFur, Charmander, Foximile, Kailys, Kauko]
    'developers': [38623, 34165, 15224, 2475, 8627],
}
staff._init_staff(staff_dict)

We recommend storing staff members in lexicographic order by name
within each group.
"""


""" Directors have the same powers as admins. """
DIRECTORS = set()

""" Technical staff can moderate all content and manage all users. """
TECHNICAL = set()

""" Site administrators can update site news and moderate user content. """
ADMINS = set()

""" Site moderators can hide submissions, manage non-admin users, etc. """
MODS = set()

""" Purely cosmetic group for users who contribute to site development. """
DEVELOPERS = set()


def _init_staff(staff_dict):
    """
    Loads staff from a yaml config file.

    Parameters:
        staff_dict: Dict containing staff levels with user IDs.
    """

    DIRECTORS.update(staff_dict['directors'])
    TECHNICAL.update(DIRECTORS, staff_dict['technical_staff'])
    ADMINS.update(DIRECTORS, TECHNICAL, staff_dict['admins'])
    MODS.update(ADMINS, staff_dict['mods'])
    DEVELOPERS.update(staff_dict['developers'])

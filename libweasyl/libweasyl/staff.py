"""
Dictionaries of Weasyl staff.

This module must be initialized with a call to `staff._init_staff()`
with the path to a yaml config file where staff members are identified
by their user id. Example contents of such a config file might look as
follows:

    directors:
        - 1014   # Fiz
        - 2061   # Ikani

    technical_staff:
        - 5756   # Weykent

    admins:  # Directors and technical_staff also have admin privs.
        - 23613  # Hendikins
        - 3      # Kihari

    mods:  # Admins also have mod privs.
        - 40212  # pinardilla

    developers:
        - 38623  # 8BitFur
        - 34165  # Charmander
        - 15224  # Foximile
        - 2475   # Kailys
        - 8627   # Kauko

We recommend storing staff members in lexicographic order by name
within each group.
"""

import yaml


DIRECTORS = set()
""" Directors have the same powers as admins. """


TECHNICAL = set()
""" Technical staff can moderate all content and manage all users. """


ADMINS = set()
""" Site administrators can update site news and moderate user content. """


MODS = set()
""" Site moderators can hide submissions, manage non-admin users, etc. """


DEVELOPERS = set()
""" Purely cosmetic group for users who contribute to site development. """


def _init_staff(staff_config_path):
    """
    Loads staff from a yaml config file.

    Parameters:
        staff_config_path: String path to a yaml file specifying staff.
    """
    with open(staff_config_path) as config_file:
        staff = yaml.safe_load(config_file)
    DIRECTORS.update(staff['directors'])
    TECHNICAL.update(DIRECTORS, staff['technical_staff'])
    ADMINS.update(DIRECTORS, TECHNICAL, staff['admins'])
    MODS.update(ADMINS, staff['mods'])
    DEVELOPERS.update(staff['developers'])

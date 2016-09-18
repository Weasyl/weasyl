"""
Retrieve a dictionary of Weasyl staff.

This module is invoked by calling `read_staff_yaml.load_staff_dict()`, and it
returns a dictionary object containing user levels and IDs loaded from
macro.MACRO_SYS_STAFF_CONFIG_PATH.

The formatting of the YAML file is as follows, containing the user id numbers
of the staff members for the respective categories:

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

from __future__ import absolute_import

import yaml

from weasyl import macro


def load_staff_dict():
    """
    Loads staff from a yaml config file.

    Parameters: None. Path is obtained from `macro.MACRO_SYS_STAFF_CONFIG_PATH`

    Returns:
        staff_dict: A dictionary with the staff member user IDs.
    """
    with open(macro.MACRO_SYS_STAFF_CONFIG_PATH) as config_file:
        return yaml.safe_load(config_file)

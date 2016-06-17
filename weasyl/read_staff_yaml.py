"""
Dictionary of Weasyl staff.

This module must be initialized with a call to `read_staff_yaml._init_staff_dict()`.
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

import yaml
from weasyl import macro


def _load_staff_dict():
    """
    Loads staff from a yaml config file.

    Parameters: None. Path is obtained from ``macro.MACRO_SYS_STAFF_CONFIG_PATH``
    
    Returns:
        staff_dict: A dictionary with the staff member user IDs.
    """
    
    load_directors = set()
    """ Directors have the same powers as admins. """
    
    
    load_technical = set()
    """ Technical staff can moderate all content and manage all users. """
    
    
    load_admins = set()
    """ Site administrators can update site news and moderate user content. """
    
    
    load_mods = set()
    """ Site moderators can hide submissions, manage non-admin users, etc. """
    
    
    load_developers = set()
    """ Purely cosmetic group for users who contribute to site development. """

    with open(macro.MACRO_SYS_STAFF_CONFIG_PATH) as config_file:
        staff = yaml.safe_load(config_file)
    load_directors.update(staff['directors'])
    load_technical.update(load_directors, staff['technical_staff'])
    load_admins.update(load_directors, load_technical, staff['admins'])
    load_mods.update(load_admins, staff['mods'])
    load_developers.update(staff['developers'])
    
    staff_dict = {
        'directors': load_directors,
        'technical_staff': load_technical,
        'admins': load_admins,
        'mods': load_mods,
        'developers': load_developers,
    }
    return staff_dict
    
    

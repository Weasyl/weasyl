"""
Retrieve a dictionary of Weasyl staff.

This module is invoked by calling `read_staff_json.load_staff_dict()`, and it
returns a dictionary object containing user levels and IDs loaded from
macro.MACRO_SYS_STAFF_CONFIG_PATH.

The formatting of the JSON file is as follows, containing the user id numbers
of the staff members for the respective categories:

{
  "staff_levels": {
    "directors": {
      "Fiz": 1014,
      "Hendikins": 23613,
      "Ikani": 2061,
      "SkylerBunny": 2402,
      "Taw": 5,
      "Tiger": 2008
    },
    "technical_staff": {
      "Keet": 5173
    },
    "admins": {
      "Kihari": 3,
      "MLR": 2011,
      "Novacaine": 20418
    },
    "mods": {
      "ChaosCalix": 61554,
      "Levi": 15712,
      "Menageriecat": 89199,
      "SuburbanFox": 2252
    },
    "developers": {
      "8BitFur": 38623,
      "Aden": 1019,
      "Charmander": 34165,
      "Foximile": 15224,
      "Weykent": 5756
    }
  }
}

We recommend storing staff members in lexicographic order by name
within each group.
"""

from __future__ import absolute_import

import json

from weasyl import macro


def load_staff_dict():
    """
    Loads staff from a json config file.

    Parameters: None. Path is obtained from `macro.MACRO_SYS_STAFF_CONFIG_PATH`

    Returns:
        A dictionary, where each:
          - Key: The name of a level of staff, as understood by Weasyl/libweasyl
          - Value: A list of userid numbers corresponding to the user in the JSON file.
    """
    with open(macro.MACRO_SYS_STAFF_CONFIG_PATH) as config_file:
        # The staff levels are all under the 'staff_levels' key, so directly extract it
        json_staff = json.load(config_file)['staff_levels']
        return {
            "directors": list(json_staff['directors'].values()),
            "technical_staff": list(json_staff['technical_staff'].values()),
            "admins": list(json_staff['admins'].values()),
            "mods": list(json_staff['mods'].values()),
            "developers": list(json_staff['developers'].values()),
        }

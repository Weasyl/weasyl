"""
Support for legacy code.

*DO NOT* use things from this module if it can be avoided at all. That is not
to say that the functionality should be duplicated, but that things in this
module are supporting old, crufty code, and newly-written code should not need
to use them.
"""

import string
import unicodedata


UNIXTIME_OFFSET = -18000
"""
The offset added to UNIX timestamps before storing them in the database.
"""


_SYSNAME_CHARACTERS = frozenset(string.ascii_lowercase + string.digits)


def get_sysname(target):
    """
    Convert a username to a login name.

    Parameters:
        target: :term:`str`.

    Returns:
        :term:`str` stripped of characters other than ASCII alphanumerics and lowercased.
    """
    normalized = unicodedata.normalize("NFD", target.lower())
    return "".join(i for i in normalized if i in _SYSNAME_CHARACTERS)

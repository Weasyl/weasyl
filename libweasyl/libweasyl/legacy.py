"""
Support for legacy code.

*DO NOT* use things from this module if it can be avoided at all. That is not
to say that the functionality should be duplicated, but that things in this
module are supporting old, crufty code, and newly-written code should not need
to use them.
"""

UNIXTIME_OFFSET = -18000
"""
The offset added to UNIX timestamps before storing them in the database.
"""


def plaintext(target):
    """
    Remove non-ASCII characters from a string.

    Parameters:
        target: :term:`unicode`.

    Returns:
        :term:`unicode` with all non-ASCII characters removed from *target*.
    """
    return ''.join(i for i in target if i.isalnum() and ord(i) < 128)


def login_name(target):
    """
    Convert a username to a login name.

    This is the same as lowercasing the result of calling :py:func:`.plaintext`
    on a string.

    Parameters:
        target: :term:`unicode`.

    Returns:
        :term:`unicode` with all non-ASCII characters removed from a lowercase
        *target*.
    """
    return plaintext(target).lower()

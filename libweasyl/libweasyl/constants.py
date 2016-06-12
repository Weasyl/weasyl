"""
Constant values.

Of course, these values might change between libweasyl versions, but it's
useful to have these values centralized instead of scattered throughout
libweasyl.
"""

from __future__ import unicode_literals

from collections import namedtuple
import enum


class Category(enum.Enum):
    """
    A class of constants for the categories of submissions.
    """
    visual = 'visual'
    literary = 'literary'
    multimedia = 'multimedia'


class Subcategory(namedtuple('Subcategory', ['value', 'title'])):
    """
    An object representing the subcategory of a submission.

    Attributes:
        value: The ordinal value stored in the database.
        title: The name of the subcategory shown to the user.
    """


SUBCATEGORIES_RAW = {
    1010: 'sketch',
    1020: 'traditional',
    1030: 'digital',
    1040: 'animation',
    1050: 'photography',
    1060: 'design / interface',
    1070: 'modeling / sculpture',
    1075: 'crafts / jewelry',
    1078: 'sewing / knitting',
    1080: 'desktop / wallpaper',
    1999: 'other visual',

    2010: 'story',
    2020: 'poetry / lyrics',
    2030: 'script / screenplay',
    2999: 'other literary',

    3010: 'original music',
    3020: 'cover version',
    3030: 'remix / mashup',
    3040: 'speech / reading',
    3500: 'embedded video',
    3999: 'other multimedia',
}

SUBCATEGORIES = {k: Subcategory(k, v) for k, v in SUBCATEGORIES_RAW.items()}
"""
All of the valid subcategories, as a dict mapping from ordinal value to
:py:class:`.Subcategory`.
"""


class ReportClosureReason(enum.Enum):
    """
    The reason for a report closure.
    """
    legacy = 'legacy'  # Only used on reports open before closure reasons were introduced.
    action_taken = 'action-taken'
    no_action_taken = 'no-action-taken'
    invalid = 'invalid'


MEBIBYTE = 1024 * 1024
"""
One mebibyte, or 1024 kibibytes.
"""


DEFAULT_LIMITS = {
    'gif': 10 * MEBIBYTE,
    'jpg': 10 * MEBIBYTE,
    'png': 10 * MEBIBYTE,
    'txt': 2 * MEBIBYTE,
    'pdf': 10 * MEBIBYTE,
    'mp3': 15 * MEBIBYTE,
    'swf': 15 * MEBIBYTE,
}
"""
The default per-filetype limits for submission files, as a dict mapping from
file type to size limit in bytes.
"""

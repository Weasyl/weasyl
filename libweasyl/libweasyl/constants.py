"""
Constant values.

Of course, these values might change between libweasyl versions, but it's
useful to have these values centralized instead of scattered throughout
libweasyl.
"""

from __future__ import unicode_literals

import enum


class Category(enum.Enum):
    """
    A class of constants for the categories of submissions.
    """
    visual = 'visual'
    literary = 'literary'
    multimedia = 'multimedia'


class ReportClosureReason(enum.Enum):
    """
    The reason for a report closure.
    """
    legacy = 'legacy'  # Only used on reports open before closure reasons were introduced.
    action_taken = 'action-taken'
    no_action_taken = 'no-action-taken'
    invalid = 'invalid'

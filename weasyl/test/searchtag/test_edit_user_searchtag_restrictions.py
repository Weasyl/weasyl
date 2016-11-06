"""
Tests the searchtag.edit_user_searchtag_restrictions() function's codepaths.

Abbreviations used in this file:
    stbl = searchtag restriction list
"""
from __future__ import absolute_import, unicode_literals

import pytest

from weasyl import searchtag
from weasyl.test import db_utils

# Test lists of tags
valid_tags = ['test', '*test', 'te*st', 'test*', 'test_too']
invalid_tags = ['*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}']
combined_tags = valid_tags + invalid_tags


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_no_prior_entries():
    """
    Verify that SQL code to add tags to the STBL works as expected. Additionally tests as a consequence of the test tag set:

    - That invalid tags are not added to the ``searchtag`` table.
    - The ``if added:``, non-global codepath adding the map into ``user_restricted_tags``
    """
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_searchtag_restrictions(user_id, tags)
    resultant_tags = searchtag.get_user_searchtag_restrictions(user_id)
    assert resultant_tags == valid_tags


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_prior_entries_test_removal_of_stbl_entry():
    # Setup
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_searchtag_restrictions(user_id, tags)
    tags_to_keep = ['test', 'te*st', 'test_too']

    # Set the new tags; AKA, remove the two defined tags
    tags = searchtag.parse_restricted_tags(", ".join(tags_to_keep))
    searchtag.edit_user_searchtag_restrictions(user_id, tags)
    resultant_tags = searchtag.get_user_searchtag_restrictions(user_id)
    assert resultant_tags == tags_to_keep


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_fully_clear_entries_after_adding_items():
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_searchtag_restrictions(user_id, tags)
    tags = set()
    searchtag.edit_user_searchtag_restrictions(user_id, tags)
    assert searchtag.get_user_searchtag_restrictions(user_id) == []

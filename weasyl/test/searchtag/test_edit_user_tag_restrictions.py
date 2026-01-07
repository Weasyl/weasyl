import pytest

from weasyl import searchtag
from weasyl.test import db_utils

# Test lists of tags
valid_tags = {'test', '*test', 'te*st', 'test*', 'test_too'}
invalid_tags = {'*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
rewritten_invalid_tags = {'a*a', '*aa'}
combined_tags = valid_tags | invalid_tags


@pytest.mark.usefixtures('db', 'cache')
def test_edit_user_tag_restrictions_with_no_prior_entries():
    """
    Verify that we can successfully set new user restricted tags
    when no existing tags have been set for a given user previously.
    """
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_tag_restrictions(user_id, tags)
    resultant_tags = set(searchtag.query_user_restricted_tags(user_id))
    assert resultant_tags == valid_tags | rewritten_invalid_tags


@pytest.mark.usefixtures('db', 'cache')
def test_edit_user_tag_restrictions_with_prior_entries_test_removal_of_entry():
    # Setup
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_tag_restrictions(user_id, tags)
    tags_to_keep = {'test', 'te*st', 'test_too'}

    # Set the new tags; AKA, remove the two defined tags
    tags = searchtag.parse_restricted_tags(", ".join(tags_to_keep))
    searchtag.edit_user_tag_restrictions(user_id, tags)
    resultant_tags = set(searchtag.query_user_restricted_tags(user_id))
    assert resultant_tags == tags_to_keep


@pytest.mark.usefixtures('db', 'cache')
def test_edit_user_tag_restrictions_fully_clear_entries_after_adding_items():
    user_id = db_utils.create_user()
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_user_tag_restrictions(user_id, tags)
    tags = set()
    searchtag.edit_user_tag_restrictions(user_id, tags)
    assert searchtag.query_user_restricted_tags(user_id) == []

from __future__ import absolute_import, unicode_literals

import pytest

from libweasyl import staff

from weasyl import define as d
from weasyl import searchtag
from weasyl.test import db_utils

user_tags = {'user_one', 'linux*', "bl*ed", "*cat"}
global_tags = {'global_one', 'windows*', 't*t', '*sheep'}
combined_tags = user_tags | global_tags


@pytest.mark.usefixtures('db')
def test_query_without_regex(monkeypatch):
    """
    Test for the codepath where the added tagids match existing STBL entries (AKA,
       no regexp needed).
    """
    user_id = db_utils.create_user()
    tags = searchtag.parse_blacklist_tags(", ".join(user_tags))
    
    # Create and get the tag IDs for the non-regex STBL tags
    non_regexp_tag_ids = {
        db_utils.create_tag("user_one"),
        db_utils.create_tag("global_one"),
    }
    
    searchtag.edit_searchtag_blacklist(user_id, tags)
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_blacklist_tags(", ".join(global_tags))
    searchtag.edit_searchtag_blacklist(director_user_id, tags, edit_global_blacklist=True)

    # Function under test
    query_result = searchtag.query_blacklisted_tags(user_id, non_regexp_tag_ids)

    for item in non_regexp_tag_ids:
        assert item in query_result


def test_query_with_regex(monkeypatch):
    """
    Test for the codepath where the added tagids do not existing STBL entries (AKA,
       regexp needed).
    """
    user_id = db_utils.create_user()
    tags = searchtag.parse_blacklist_tags(", ".join(user_tags))
    searchtag.edit_searchtag_blacklist(user_id, tags)
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_blacklist_tags(", ".join(global_tags))
    searchtag.edit_searchtag_blacklist(director_user_id, tags, edit_global_blacklist=True)

    # Create tag IDs for tags which will eventually match the STBL query
    tagids_matching_regexp_pattern = {
        db_utils.create_tag("linuxmint"),
        db_utils.create_tag("blocked"),
        db_utils.create_tag("kittycat"),
        db_utils.create_tag("windows_millenium"),
        db_utils.create_tag("test"),
        db_utils.create_tag("firesheep"),
    }

    # Function under test
    query_result = searchtag.query_blacklisted_tags(user_id, tagids_matching_regexp_pattern)

    for item in tagids_matching_regexp_pattern:
        assert item in query_result

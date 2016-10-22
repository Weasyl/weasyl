from __future__ import absolute_import

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
    searchtag.edit_searchtag_blacklist(user_id, user_tags)
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    searchtag.edit_searchtag_blacklist(director_user_id, global_tags, edit_global_blacklist=True)

    query = d.engine.execute("""
        SELECT tagid, title
        FROM searchtag
        WHERE title = ANY (%(tags)s)
    """, tags=list(x for x in combined_tags)).fetchall()

    non_regexp_tag_ids = {x.tagid for x in query if not x.title.count("*")}

    # Function under test
    query_result = searchtag.query_blacklisted_tags(non_regexp_tag_ids, user_id)

    for item in non_regexp_tag_ids:
        assert item in query_result


def test_query_with_regex(monkeypatch):
    """
    Test for the codepath where the added tagids do not existing STBL entries (AKA,
       regexp needed).
    """
    user_id = db_utils.create_user()
    searchtag.edit_searchtag_blacklist(user_id, user_tags)
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    searchtag.edit_searchtag_blacklist(director_user_id, global_tags, edit_global_blacklist=True)

    tagids_matching_regexp_pattern = {
        db_utils.create_tag("linuxmint"),
        db_utils.create_tag("blocked"),
        db_utils.create_tag("kittycat"),
        db_utils.create_tag("windows_millenium"),
        db_utils.create_tag("test"),
        db_utils.create_tag("firesheep"),
    }

    # Function under test
    query_result = searchtag.query_blacklisted_tags(tagids_matching_regexp_pattern, user_id)

    assert len(query_result) == len(tagids_matching_regexp_pattern)
    for item in tagids_matching_regexp_pattern:
        assert item in query_result

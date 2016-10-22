"""
Tests the searchtag.edit_searchtag_blacklist() function's codepaths.

Abbreviations used in this file:
    stbl = searchtag blacklist
"""
from __future__ import absolute_import

import pytest

from libweasyl import staff

from weasyl import searchtag
from weasyl.error import WeasylError
from weasyl.test import db_utils

# Test set of tags
valid_tags = {'test*', '*test', 'te*st', 'test', 'test_too'}
invalid_tags = {'*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
combined_tags = valid_tags | invalid_tags


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_no_prior_entries():
    """
    Verify that SQL code to add tags to the STBL works as expected. Additionally tests as a consequence of the test tag set:
    
    - That invalid tags are not added to the ``searchtag`` table.
    - The ``if added:``, non-global codepath adding the map into ``searchmapuserblacklist``
    """
    user_id = db_utils.create_user()
    searchtag.edit_searchtag_blacklist(user_id, combined_tags)
    resultant_tags = searchtag.get_searchtag_blacklist(user_id)
    assert len(resultant_tags) == len(valid_tags)
    for result in valid_tags:
        assert result in resultant_tags
    for result in invalid_tags:
        assert result not in resultant_tags


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_prior_entries_test_removal_of_stbl_entry():
    # Setup
    user_id = db_utils.create_user()
    searchtag.edit_searchtag_blacklist(user_id, combined_tags)

    tags_to_remove = {'test*', '*test'}
    tags_to_keep = {'te*st', 'test', 'test_too'}
    # Set the new tags; AKA, remove the two defined tags
    searchtag.edit_searchtag_blacklist(user_id, tags_to_keep)

    resultant_tags = searchtag.get_searchtag_blacklist(user_id)
    assert len(resultant_tags) == len(tags_to_keep)
    for kept in tags_to_keep:
        assert kept in resultant_tags
    for removed in tags_to_remove:
        assert removed not in resultant_tags


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_fully_clear_entries_after_adding_items():
    user_id = db_utils.create_user()
    searchtag.edit_searchtag_blacklist(user_id, combined_tags)
    searchtag.edit_searchtag_blacklist(user_id, {})
    assert searchtag.get_searchtag_blacklist(user_id) == []


@pytest.mark.usefixtures('db')
def test_edit_global_stbl_when_user_is_not_a_director_fails(monkeypatch):
    normal_user_id = db_utils.create_user()
    developer_user_id = db_utils.create_user()
    mod_user_id = db_utils.create_user()
    admin_user_id = db_utils.create_user()
    technical_user_id = db_utils.create_user()

    monkeypatch.setattr(staff, 'DEVELOPERS', frozenset([developer_user_id]))
    monkeypatch.setattr(staff, 'MODS', frozenset([mod_user_id]))
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user_id]))
    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([technical_user_id]))

    # Function under test; users and staff (except director) should error
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(normal_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(developer_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(mod_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(admin_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(technical_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value


@pytest.mark.usefixtures('db')
def test_edit_global_stbl(monkeypatch):
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    searchtag.edit_searchtag_blacklist(director_user_id, combined_tags, edit_global_blacklist=True)
    resultant_tags = searchtag.get_searchtag_blacklist(director_user_id, global_blacklist=True)
    assert len(resultant_tags) == len(valid_tags)
    resultant_tags_titles = {x.title for x in resultant_tags}
    for result in valid_tags:
        assert result in resultant_tags_titles

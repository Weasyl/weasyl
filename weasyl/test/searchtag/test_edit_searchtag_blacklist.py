"""
Tests the searchtag.edit_searchtag_blacklist() function's codepaths.

Abbreviations used in this file:
    stbl = searchtag blacklist
"""
from __future__ import absolute_import

import pytest

from libweasyl import staff

from weasyl import define as d
from weasyl import searchtag
from weasyl.error import WeasylErrror
from weasyl.test import db_utils

# Test set of tags
valid_tags = set(['test*', '*test', 'te*st', 'test', 'test_too'])
invalid_tags = set(['*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'])
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
    for result in resultant_tags:
        assert result in valid_tags
    for result in resultant_tags:
        assert result not in invalid_tags
    pass
    
@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_prior_entries_test_no_duplicates():
    """
    Verifies that if a user attempts to add a duplicate STBL entry, the code does not result in duplication.
    
    E.g., user has 'apple', tries to add 'apple', verify that the resultant rows only have 'apple' once.
    """
    user_id = db_utils.create_user()
    pass


@pytest.mark.usefixtures('db')
def test_edit_user_stbl_with_prior_entries_test_removal_of_stbl_entry():
    user_id = db_utils.create_user()
    pass


@pytest.mark.usefixtures('db')
def test_edit_global_stbl_when_user_is_not_a_director_fails(monkeypatch):
    normal_user_id = db_utils.create_user()
    developer_user_id = db_utils.create_user()
    mod_user_id = db_utils.create_user()
    admin_user_id = db_utils.create_user()
    technical_user_id = db_utils.create_user()

    # Monkeypatch the staff global variables
    monkeypatch.setattr(staff, 'DEVELOPER', frozenset([developer_user_id]))
    monkeypatch.setattr(staff, 'MODS', frozenset([mod_user_id]))
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user_id]))
    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([technical_user_id]))

    # Test normal user accounts
    with pytest.raises(WeasylError) as err:
        searchtag.edit_searchtag_blacklist(normal_user_id, combined_tags, edit_global_blacklist=True)
    assert 'InsufficientPermissions' == err.value.value

    # Test higher elevated users (except directors)
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
    # Monkeypatch the director global variable
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    pass

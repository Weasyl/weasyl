from __future__ import absolute_import, unicode_literals

import pytest

from libweasyl import staff

from weasyl import searchtag
from weasyl.error import WeasylError
from weasyl.test import db_utils

# Test lists of tags
valid_tags = {'test', '*test', 'te*st', 'test*', 'test_too'}
invalid_tags = {'*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
combined_tags = valid_tags | invalid_tags


@pytest.mark.usefixtures('db')
def test_edit_global_tag_restrictions_fully_clear_entries_after_adding_items(monkeypatch):
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    tags = set()
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    assert searchtag.get_global_tag_restrictions(director_user_id) == {}


@pytest.mark.usefixtures('db')
def test_edit_global_tag_restrictions_when_user_is_not_a_director_fails(monkeypatch):
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
        searchtag.edit_global_tag_restrictions(normal_user_id, combined_tags)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_global_tag_restrictions(developer_user_id, combined_tags)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_global_tag_restrictions(mod_user_id, combined_tags)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_global_tag_restrictions(admin_user_id, combined_tags)
    assert 'InsufficientPermissions' == err.value.value
    with pytest.raises(WeasylError) as err:
        searchtag.edit_global_tag_restrictions(technical_user_id, combined_tags)
    assert 'InsufficientPermissions' == err.value.value


@pytest.mark.usefixtures('db')
def test_edit_global_tag_restrictions(monkeypatch):
    director_user_id = db_utils.create_user(username="testdirector")
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    resultant_tags = searchtag.get_global_tag_restrictions(director_user_id)
    assert set(resultant_tags.keys()) == valid_tags
    assert set(resultant_tags.values()) == {"testdirector"}

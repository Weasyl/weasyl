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
def test_get_global_searchtag_restrictions(monkeypatch):
    director_user_id = db_utils.create_user(username="testdirector")
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    resultant_tags = searchtag.get_global_tag_restrictions(director_user_id)
    assert set(resultant_tags.keys()) == valid_tags
    assert set(resultant_tags.values()) == {"testdirector"}


@pytest.mark.usefixtures('db')
def test_get_global_searchtag_restrictions_fails_for_non_directors(monkeypatch):
    # Setup the globally restricted tags list
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)

    normal_user_id = db_utils.create_user()
    developer_user_id = db_utils.create_user()
    mod_user_id = db_utils.create_user()
    admin_user_id = db_utils.create_user()
    technical_user_id = db_utils.create_user()

    # Monkeypatch the staff global variables
    monkeypatch.setattr(staff, 'DEVELOPERS', frozenset([developer_user_id]))
    monkeypatch.setattr(staff, 'MODS', frozenset([mod_user_id]))
    monkeypatch.setattr(staff, 'ADMINS', frozenset([admin_user_id]))
    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([technical_user_id]))

    with pytest.raises(WeasylError) as err:
        searchtag.get_global_tag_restrictions(normal_user_id)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_global_tag_restrictions(developer_user_id)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_global_tag_restrictions(mod_user_id)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_global_tag_restrictions(admin_user_id)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_global_tag_restrictions(technical_user_id)
    assert err.value.value == 'InsufficientPermissions'

from __future__ import absolute_import

import pytest

from libweasyl import staff

from weasyl import searchtag
from weasyl.error import WeasylError
from weasyl.test import db_utils

valid_tags = set(['test*', '*test', 'te*st', 'test', 'test_too'])
invalid_tags = set(['*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'])
combined_tags = valid_tags | invalid_tags


@pytest.mark.usefixtures('db')
def test_get_user_searchtag_blacklist():
    user_id = db_utils.create_user()
    searchtag.edit_searchtag_blacklist(user_id, combined_tags)
    resultant_tags = searchtag.get_searchtag_blacklist(user_id)
    for result in resultant_tags:
        assert result in valid_tags
    for result in resultant_tags:
        assert result not in invalid_tags


@pytest.mark.usefixtures('db')
def test_get_global_searchtag_blacklist(monkeypatch):
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    searchtag.edit_searchtag_blacklist(director_user_id, combined_tags, edit_global_blacklist=True)
    resultant_tags = searchtag.get_searchtag_blacklist(director_user_id, global_blacklist=True)
    for result in resultant_tags:
        assert result.title in valid_tags
    for result in resultant_tags:
        assert result.title not in invalid_tags


@pytest.mark.usefixtures('db')
def test_get_global_searchtag_blacklist_fails_for_non_directors(monkeypatch):
    # Setup the Global STBL
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    searchtag.edit_searchtag_blacklist(director_user_id, combined_tags, edit_global_blacklist=True)

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
        searchtag.get_searchtag_blacklist(normal_user_id, global_blacklist=True)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_searchtag_blacklist(developer_user_id, global_blacklist=True)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_searchtag_blacklist(mod_user_id, global_blacklist=True)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_searchtag_blacklist(admin_user_id, global_blacklist=True)
    assert err.value.value == 'InsufficientPermissions'

    with pytest.raises(WeasylError) as err:
        searchtag.get_searchtag_blacklist(technical_user_id, global_blacklist=True)
    assert err.value.value == 'InsufficientPermissions'

import pytest

from libweasyl import staff

from weasyl import searchtag
from weasyl.test import db_utils

# Test lists of tags
valid_tags = {'test', '*test', 'te*st', 'test*', 'test_too'}
invalid_tags = {'*', 'a*', '*a', 'a*a*', '*a*a', '*aa*', 'a**a', '}'}
rewritten_invalid_tags = {'a*a', '*aa'}
combined_tags = valid_tags | invalid_tags


@pytest.mark.usefixtures('db', 'cache')
def test_edit_global_tag_restrictions_fully_clear_entries_after_adding_items(monkeypatch):
    director_user_id = db_utils.create_user()
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    tags = set()
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    assert searchtag.get_global_tag_restrictions() == {}


@pytest.mark.usefixtures('db', 'cache')
def test_edit_global_tag_restrictions(monkeypatch):
    director_user_id = db_utils.create_user(username="testdirector")
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director_user_id]))
    tags = searchtag.parse_restricted_tags(", ".join(combined_tags))
    searchtag.edit_global_tag_restrictions(director_user_id, tags)
    resultant_tags = searchtag.get_global_tag_restrictions()
    assert set(resultant_tags.keys()) == valid_tags | rewritten_invalid_tags
    assert set(resultant_tags.values()) == {"testdirector"}

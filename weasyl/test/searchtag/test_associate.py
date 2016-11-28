from __future__ import absolute_import, unicode_literals

import pytest

from libweasyl import staff
from libweasyl.models.helpers import CharSettings

from weasyl import profile, searchtag
from weasyl.error import WeasylError
from weasyl.test import db_utils

# Tag sets for testing
tags = searchtag.parse_tags("omega_ruby, alpha_sapphire, diamond, pearl")
tags_two = searchtag.parse_tags("omega_ruby, alpha_sapphire, diamond")


@pytest.mark.usefixtures('db')
def test_TargetRecordMissing_WeasylError_if_item_record_missing_or_invalid():
    userid_tag_adder = db_utils.create_user()

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, submitid=666)
    assert err.value.value == "TargetRecordMissing"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, charid=666)
    assert err.value.value == "TargetRecordMissing"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, journalid=666)
    assert err.value.value == "TargetRecordMissing"


@pytest.mark.usefixtures('db')
def test_InsufficientPermissions_WeasylError_if_user_does_not_have_tagging_permissions():
    # Set up for this test
    admin = db_utils.create_user()
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    profile.do_manage(admin, userid_tag_adder, permission_tag=False)

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    assert err.value.value == "InsufficientPermissions"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, charid=charid)
    assert err.value.value == "InsufficientPermissions"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, journalid=journalid)
    assert err.value.value == "InsufficientPermissions"


@pytest.mark.usefixtures('db')
def test_contentOwnerIgnoredYou_WeasylError_if_user_ignored_by_item_owner():
    # Set up for this test
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    db_utils.create_ignoreuser(userid_owner, userid_tag_adder)

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    assert err.value.value == "contentOwnerIgnoredYou"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, charid=charid)
    assert err.value.value == "contentOwnerIgnoredYou"

    with pytest.raises(WeasylError) as err:
        searchtag.associate(userid_tag_adder, tags, journalid=journalid)
    assert err.value.value == "contentOwnerIgnoredYou"


@pytest.mark.usefixtures('db')
def test_adding_tags_when_no_tags_previously_existed():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)

    searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    searchtag.associate(userid_tag_adder, tags, charid=charid)
    searchtag.associate(userid_tag_adder, tags, journalid=journalid)

    submission_tags = searchtag.select(submitid=submitid)
    assert tags == set(submission_tags)

    character_tags = searchtag.select(charid=charid)
    assert tags == set(character_tags)

    journal_tags = searchtag.select(journalid=journalid)
    assert tags == set(journal_tags)


@pytest.mark.usefixtures('db')
def test_removing_tags():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    searchtag.associate(userid_tag_adder, tags, charid=charid)
    searchtag.associate(userid_tag_adder, tags, journalid=journalid)

    # Remove the 'pearl' tag
    searchtag.associate(userid_tag_adder, tags_two, submitid=submitid)
    searchtag.associate(userid_tag_adder, tags_two, charid=charid)
    searchtag.associate(userid_tag_adder, tags_two, journalid=journalid)

    submission_tags = searchtag.select(submitid=submitid)
    assert tags_two == set(submission_tags)

    character_tags = searchtag.select(charid=charid)
    assert tags_two == set(character_tags)

    journal_tags = searchtag.select(journalid=journalid)
    assert tags_two == set(journal_tags)


@pytest.mark.usefixtures('db')
def test_clearing_all_tags():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    searchtag.associate(userid_tag_adder, tags, charid=charid)
    searchtag.associate(userid_tag_adder, tags, journalid=journalid)

    # Clear all tags now that they were initially set
    empty_tags = set()
    searchtag.associate(userid_tag_adder, empty_tags, submitid=submitid)
    searchtag.associate(userid_tag_adder, empty_tags, charid=charid)
    searchtag.associate(userid_tag_adder, empty_tags, journalid=journalid)

    submitid_tags = searchtag.select(submitid=submitid)
    assert submitid_tags == []

    charid_tags = searchtag.select(charid=charid)
    assert charid_tags == []

    journalid_tags = searchtag.select(journalid=journalid)
    assert journalid_tags == []


@pytest.mark.usefixtures('db')
def test_attempt_setting_tags_when_some_tags_have_been_restricted():
    """
    Verify that tags are excluded from being added to a submission's tags if the tag is restricted
    """
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    restricted_tag = searchtag.parse_restricted_tags("pearl")
    searchtag.edit_user_tag_restrictions(userid_owner, restricted_tag)

    searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    searchtag.associate(userid_tag_adder, tags, charid=charid)
    searchtag.associate(userid_tag_adder, tags, journalid=journalid)

    # Verify that the "pearl" tag was not added
    submission_tags = searchtag.select(submitid=submitid)
    assert tags_two == set(submission_tags)

    character_tags = searchtag.select(charid=charid)
    assert tags_two == set(character_tags)

    journal_tags = searchtag.select(journalid=journalid)
    assert tags_two == set(journal_tags)


@pytest.mark.usefixtures('db')
def test_moderators_and_above_can_add_restricted_tags_successfully(monkeypatch):
    """
    Moderators (and admins, technical, and directors) can add restricted tags to content.
    Developers are not included in this test, as they are for all intents and purposes just
      normal user accounts.
    """
    userid_owner = db_utils.create_user()
    mod_tag_adder = db_utils.create_user()
    monkeypatch.setattr(staff, 'MODS', frozenset([mod_tag_adder]))
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    restricted_tag = searchtag.parse_restricted_tags("pearl")
    searchtag.edit_user_tag_restrictions(userid_owner, restricted_tag)

    searchtag.associate(mod_tag_adder, tags, submitid=submitid)
    searchtag.associate(mod_tag_adder, tags, charid=charid)
    searchtag.associate(mod_tag_adder, tags, journalid=journalid)

    # Verify that all tags were added successfully. 'pearl' is restricted.
    submission_tags = searchtag.select(submitid=submitid)
    assert tags == set(submission_tags)

    character_tags = searchtag.select(charid=charid)
    assert tags == set(character_tags)

    journal_tags = searchtag.select(journalid=journalid)
    assert tags == set(journal_tags)


@pytest.mark.usefixtures('db')
def test_associate_return_values():
    """
    ``associate()`` returns a dict, of the following format:
    return {"add_failure_restricted_tags": add_failure_restricted_tags,
            "remove_failure_owner_set_tags": remove_failure_owner_set_tags}
    /OR/ None

    add_failure_restricted_tags is None if no tags failed to be added during the associate call,
    when due to a tag being on the user or globally restricted tags list. Otherwise, it contains
    a space-separated list of tags which failed to be added to the content item.

    remove_failure_owner_set_tags is None if no tags failed to be removed during the associate call.
    Otherwise, it contains the same space-separated list as above, however containing tags which the
    content owner added and has opted to not permit others to remove.

    If neither element of the dict is set, ``associate()`` returns None.
    """
    config = CharSettings({'disallow-others-tag-removal'}, {}, {})
    userid_owner = db_utils.create_user(config=config)
    userid_tag_adder = db_utils.create_user()
    submitid = db_utils.create_submission(userid_owner)
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)

    """ Test the None result (no failures), then manually clear the tags afterwards. """
    result = searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    assert result is None
    result = searchtag.associate(userid_tag_adder, tags, journalid=journalid)
    assert result is None
    result = searchtag.associate(userid_tag_adder, tags, journalid=journalid)
    assert result is None
    searchtag.associate(userid_tag_adder, set(), submitid=submitid)
    searchtag.associate(userid_tag_adder, set(), journalid=journalid)
    searchtag.associate(userid_tag_adder, set(), journalid=journalid)

    """ Test the result:None variant (restricted tags added, no tags removed) """
    restricted_tag = searchtag.parse_restricted_tags("pearl")
    searchtag.edit_user_tag_restrictions(userid_owner, restricted_tag)
    result = searchtag.associate(userid_tag_adder, tags, submitid=submitid)
    assert "pearl" in result["add_failure_restricted_tags"]
    assert result["remove_failure_owner_set_tags"] is None
    result = searchtag.associate(userid_tag_adder, tags, charid=charid)
    assert "pearl" in result["add_failure_restricted_tags"]
    assert result["remove_failure_owner_set_tags"] is None
    result = searchtag.associate(userid_tag_adder, tags, journalid=journalid)
    assert "pearl" in result["add_failure_restricted_tags"]
    assert result["remove_failure_owner_set_tags"] is None
    searchtag.associate(userid_owner, set(), submitid=submitid)
    searchtag.associate(userid_owner, set(), charid=charid)
    searchtag.associate(userid_owner, set(), journalid=journalid)
    searchtag.edit_user_tag_restrictions(userid_owner, set())

    """Test the None:result variant (no restricted tags added, tag removal blocked)
    - Submission items will return None in this case (different method of preventing tag removal)
    - Character and journal items should return the None:result variant, as expected"""
    searchtag.associate(userid_owner, tags, submitid=submitid)
    searchtag.associate(userid_owner, tags, charid=charid)
    searchtag.associate(userid_owner, tags, journalid=journalid)
    result = searchtag.associate(userid_tag_adder, tags_two, submitid=submitid)
    assert result is None
    result = searchtag.associate(userid_tag_adder, tags_two, charid=charid)
    assert result["add_failure_restricted_tags"] is None
    assert "pearl" in result["remove_failure_owner_set_tags"]
    result = searchtag.associate(userid_tag_adder, tags_two, journalid=journalid)
    assert result["add_failure_restricted_tags"] is None
    assert "pearl" in result["remove_failure_owner_set_tags"]
    searchtag.associate(userid_owner, set(), submitid=submitid)
    searchtag.associate(userid_owner, set(), charid=charid)
    searchtag.associate(userid_owner, set(), journalid=journalid)

    """Test the result:result variant (restricted tags added, tag removal blocked)
    - Submission items will behave in the result:None variant
    - Character/Journal items will behave in the result:result manner"""
    restricted_tag = searchtag.parse_restricted_tags("profanity")
    searchtag.edit_user_tag_restrictions(userid_owner, restricted_tag)
    searchtag.associate(userid_owner, tags, submitid=submitid)
    searchtag.associate(userid_owner, tags, charid=charid)
    searchtag.associate(userid_owner, tags, journalid=journalid)
    # Effect upon adding this set: Remove user-set tag "pearl"; add restricted tag "profanity"
    tags_three = tags_two | {"profanity"}
    result = searchtag.associate(userid_tag_adder, tags_three, submitid=submitid)
    assert "profanity" in result["add_failure_restricted_tags"]
    assert result["remove_failure_owner_set_tags"] is None
    result = searchtag.associate(userid_tag_adder, tags_three, charid=charid)
    assert "profanity" in result["add_failure_restricted_tags"]
    assert "pearl" in result["remove_failure_owner_set_tags"]
    result = searchtag.associate(userid_tag_adder, tags_three, journalid=journalid)
    assert "profanity" in result["add_failure_restricted_tags"]
    assert "pearl" in result["remove_failure_owner_set_tags"]

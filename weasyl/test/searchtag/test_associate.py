import pytest

from libweasyl import staff

from weasyl import profile, searchtag
from weasyl.error import WeasylError
from weasyl.searchtag import GroupedTags
from weasyl.test import db_utils

# Tag sets for testing
tags = searchtag.parse_tags("omega_ruby, alpha_sapphire, diamond, pearl")
tags_two = searchtag.parse_tags("omega_ruby, alpha_sapphire, diamond")


@pytest.mark.usefixtures('db', 'cache')
def test_TargetRecordMissing_WeasylError_if_item_record_missing_or_invalid():
    userid_tag_adder = db_utils.create_user()

    targets = [
        f(666)
        for f in (
            searchtag.SubmissionTarget,
            searchtag.CharacterTarget,
            searchtag.JournalTarget,
        )
    ]

    for target in targets:
        with pytest.raises(WeasylError) as err:
            searchtag.associate(
                userid=userid_tag_adder,
                target=target,
                tag_names=tags,
            )
        assert err.value.value == "TargetRecordMissing"


@pytest.mark.usefixtures('db', 'cache')
def test_InsufficientPermissions_WeasylError_if_user_does_not_have_tagging_permissions():
    # Set up for this test
    admin = db_utils.create_user()
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    profile.do_manage(admin, userid_tag_adder, permission_tag=False)
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )

    for target in targets:
        with pytest.raises(WeasylError) as err:
            searchtag.associate(
                userid=userid_tag_adder,
                target=target,
                tag_names=tags,
            )
        assert err.value.value == "InsufficientPermissions"


@pytest.mark.usefixtures('db', 'cache')
def test_contentOwnerIgnoredYou_WeasylError_if_user_ignored_by_item_owner():
    # Set up for this test
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    db_utils.create_ignoreuser(userid_owner, userid_tag_adder)
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )

    for target in targets:
        with pytest.raises(WeasylError) as err:
            searchtag.associate(
                userid=userid_tag_adder,
                target=target,
                tag_names=tags,
            )
        assert err.value.value == "contentOwnerIgnoredYou"


@pytest.mark.usefixtures('db', 'cache')
def test_adding_tags_when_no_tags_previously_existed():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )

        assert set(searchtag.select_grouped(userid_owner, target).suggested) == tags


@pytest.mark.usefixtures('db', 'cache')
def test_removing_tags():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )

    # Remove the 'pearl' tag
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags_two,
        )

        assert set(searchtag.select_grouped(userid_owner, target).suggested) == tags_two


@pytest.mark.usefixtures('db', 'cache')
def test_clearing_all_tags():
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)
    submitid = db_utils.create_submission(userid_owner)
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )

    # Clear all tags now that they were initially set
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=set(),
        )

        assert searchtag.select_grouped(userid_owner, target) == GroupedTags(
            artist=[],
            suggested=[],
            own_suggested=[],
        )


@pytest.mark.usefixtures('db', 'cache')
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
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )

        # Verify that the "pearl" tag was not added
        assert set(searchtag.select_grouped(userid_owner, target).suggested) == tags_two


@pytest.mark.usefixtures('db', 'cache')
def test_moderators_and_above_can_add_restricted_tags_successfully(monkeypatch):
    """
    Moderators (and admins and directors) can add restricted tags to content.
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
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        searchtag.associate(
            userid=mod_tag_adder,
            target=target,
            tag_names=tags,
        )

    # Verify that all tags were added successfully. 'pearl' is restricted.
    submission_tags = searchtag.select(submitid=submitid)
    assert tags == set(submission_tags)

    character_tags = searchtag.select(charid=charid)
    assert tags == set(character_tags)

    journal_tags = searchtag.select(journalid=journalid)
    assert tags == set(journal_tags)


@pytest.mark.usefixtures('db', 'cache')
def test_associate_return_values():
    """
    ``associate()`` returns a list of tags that were not added because of restrictions.
    """
    userid_owner = db_utils.create_user()
    userid_tag_adder = db_utils.create_user()
    submitid = db_utils.create_submission(userid_owner)
    journalid = db_utils.create_journal(userid_owner)
    charid = db_utils.create_character(userid_owner)

    """ Test the empty result (no failures), then manually clear the tags afterwards. """
    targets = (
        searchtag.SubmissionTarget(submitid),
        searchtag.CharacterTarget(charid),
        searchtag.JournalTarget(journalid),
    )
    for target in targets:
        result = searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )
        assert result == []
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=set(),
        )

    """ Test restricted tags added. """
    restricted_tag = searchtag.parse_restricted_tags("pearl")
    searchtag.edit_user_tag_restrictions(userid_owner, restricted_tag)
    for target in targets:
        result = searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=tags,
        )
        assert "pearl" in result
        searchtag.associate(
            userid=userid_tag_adder,
            target=target,
            tag_names=set(),
        )
    searchtag.edit_user_tag_restrictions(userid_owner, set())

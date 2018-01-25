from __future__ import absolute_import, unicode_literals

import pytest

from libweasyl import staff
from weasyl import define as d
from weasyl import note
from weasyl import shout
from weasyl.error import WeasylError
from weasyl.test import db_utils
from weasyl.test.utils import Bag
from weasyl.test.web.wsgi import app


def _make_test_note(recipient="user2", title="ThisIsATestNote", content="ThisIsTheTestContent", mod_copy='', staff_note=''):
    return Bag(
        recipient=recipient,
        title=title,
        content=content,
        mod_copy=mod_copy,
        staff_note=staff_note,
    )


def _set_user_note_config(userid=None, set_note_config=None):
    """
    Set the note configuration for a user
    :param userid:
    :param set_note_config: 'z' is friends only notes, 'y' is staff only, 'anyone' is all users
    :return: Nothing.
    """
    cookie = db_utils.create_session(userid)
    payload = {
        'rating': 10,
        'sfwrating': 10,
        'timezone': 'America/Dawson',
        'notes': set_note_config if set_note_config is not None else "anyone",
    }
    app.post(url='/control/editpreferences', params=payload, headers={'Cookie': cookie})


@pytest.fixture(autouse=True)
def create_users():
    return {"user" + str(i + 1): db_utils.create_user(username='user' + str(i + 1)) for i in range(12)}


class TestSendFunction(object):
    @pytest.mark.usefixtures('db')
    def test_contentInvalid_if_no_content(self, create_users):
        test_case_note = _make_test_note(content='')
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "contentInvalid"

    @pytest.mark.usefixtures('db')
    def test_titleInvalid_if_no_title(self, create_users):
        test_case_note = _make_test_note(title='')
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "titleInvalid"

    @pytest.mark.usefixtures('db')
    def test_titleInvalid_if_title_too_long(self, create_users):
        test_case_note = _make_test_note(title="a" * 101)
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "titleTooLong"

    @pytest.mark.usefixtures('db')
    def test_recipientInvalid_if_messaging_self(self, create_users):
        test_case_note = _make_test_note(recipient="user1")
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "recipientInvalid"

    @pytest.mark.usefixtures('db')
    def test_recipientInvalid_if_messaging_an_ignored_user(self, create_users):
        # When user1 ignores user2
        test_case_note = _make_test_note()
        test_case_note.recipient = "user2"
        db_utils.create_ignoreuser(create_users['user1'], create_users['user2'])
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "recipientInvalid"

    @pytest.mark.usefixtures('db')
    def test_recipientInvalid_if_recipient_ignores_sender(self, create_users):
        # When user2 ignores user1
        test_case_note = _make_test_note()
        db_utils.create_ignoreuser(create_users['user2'], create_users['user1'])
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "recipientInvalid"

    @pytest.mark.usefixtures('db', 'no_csrf')
    def test_only_receive_notes_from_friends_otherwise_recipientInvalid(self, create_users):
        # User 1 <FriendsWith> User2, but not User3
        # Corresponds to the "Allow only friends to send me private messages" setting
        test_case_note = _make_test_note(recipient="user1")
        # User one only can receives notes from friends.
        _set_user_note_config(userid=create_users['user1'], set_note_config='z')
        db_utils.create_friendship(create_users['user1'], create_users['user2'])
        with pytest.raises(WeasylError) as err:
            # user3 can't send to user1
            note.send(create_users['user3'], test_case_note)
        assert err.value.value == "recipientInvalid"

        # This, however, should not error (user2 -> user1)
        note.send(create_users['user2'], test_case_note)
        query = d.engine.execute("""
            SELECT * FROM message
            WHERE userid = %(note_sender)s AND otherid = %(note_recipient)s
        """, note_sender=create_users['user2'], note_recipient=create_users['user1']).first()
        query_debug = d.engine.execute("""
            SELECT * FROM message;
        """).fetchall()

        assert query['content'] == test_case_note.content

    @pytest.mark.usefixtures('db', 'no_csrf')
    def test_only_receive_notes_from_staff_otherwise_recipientInvalid(self, monkeypatch, create_users):
        # user2/3/4/5/6 is a mod/admin/director/technical/dev respectively; user7 is a normal user.
        # Corresponds to the "Allow only friends to send me private messages" setting
        mod = create_users["user2"]
        admin = create_users['user3']
        director = create_users['user4']
        technical = create_users['user5']
        # A dev is a "normal" user. The dev and user6 are expected to error.
        dev = create_users['user6']

        # Force-set the staff list
        monkeypatch.setattr(staff, 'DEVELOPERS', frozenset([dev]))
        monkeypatch.setattr(staff, 'TECHNICAL', frozenset([technical, director]))
        monkeypatch.setattr(staff, 'MODS', frozenset([mod, admin, technical, director]))
        monkeypatch.setattr(staff, 'ADMINS', frozenset([admin, technical, director]))
        monkeypatch.setattr(staff, 'DIRECTORS', frozenset([director]))

        # User one only can receives notes from staff (2/3/4/5).
        _set_user_note_config(userid=create_users['user1'], set_note_config='y')

        test_case_note = _make_test_note(recipient="user1")

        for userid in [dev, create_users['user7']]:
            with pytest.raises(WeasylError) as err:
                # Devs and normal users are not staff, so will result in recipientInvalid
                note.send(userid, test_case_note)
            assert err.value.value == "recipientInvalid"

        # Staff (mods and above) can message user1, however.
        for userid in [mod, admin, director, technical]:
            note.send(userid, test_case_note)
            query = d.engine.execute("""
                SELECT * FROM message
                WHERE userid = %(note_sender)s AND otherid = %(note_recipient)s
            """, note_sender=userid, note_recipient=create_users['user1']).first()
            assert query['content'] == test_case_note.content

    @pytest.mark.usefixtures('db')
    def test_over_ten_recipients_raises_recipientExcessive(self, create_users):
        test_case_note = _make_test_note(recipient="; ".join(create_users.keys()))
        with pytest.raises(WeasylError) as err:
            note.send(create_users['user1'], test_case_note)
        assert err.value.value == "recipientExcessive"

    @pytest.mark.usefixtures('db')
    def test_sending_succeeds_if_only_some_recipients_ignored(self, create_users):
        # user1 ignores user2/user3; user4 is not ignored
        test_case_note = _make_test_note(recipient="user2; user3; user4")
        db_utils.create_ignoreuser(create_users['user1'], create_users['user2'])
        db_utils.create_ignoreuser(create_users['user1'], create_users['user3'])

        note.send(create_users['user1'], test_case_note)
        query = d.engine.execute("""
                    SELECT * FROM message
                """).fetchall()  # , note_sender=userid, note_recipient=create_users['user1']).first()
        assert len(query) == 1
        assert query[0]['content'] == test_case_note.content
        assert query[0]['userid'] == create_users['user1']
        assert query[0]['otherid'] == create_users['user4']

    @pytest.mark.usefixtures('db')
    def test_sending_succeeds_if_not_all_recipients_ignore_sender(self, create_users):
        # user1 is ignored by user2/user3; user4 does not ignore user1
        test_case_note = _make_test_note(recipient="user2; user3; user4")
        db_utils.create_ignoreuser(create_users['user2'], create_users['user1'])
        db_utils.create_ignoreuser(create_users['user3'], create_users['user1'])

        note.send(create_users['user1'], test_case_note)

        query = d.engine.execute("""
            SELECT * FROM message
        """).fetchall()  # , note_sender=userid, note_recipient=create_users['user1']).first()
        assert len(query) == 1
        assert query[0]['content'] == test_case_note.content
        assert query[0]['userid'] == create_users['user1']
        assert query[0]['otherid'] == create_users['user4']

    @pytest.mark.usefixtures('db')
    def test_mod_copy_when_sender_not_mod(self, create_users, monkeypatch):
        test_case_note = _make_test_note(recipient="user2", mod_copy='y')

        note.send(create_users['user1'], test_case_note)

        result = shout.select(userid=create_users['user1'], ownerid=create_users['user2'], staffnotes=True)

        assert len(result) == 0
        assert isinstance(result, list)

    @pytest.mark.usefixtures('db')
    def test_mod_copy_when_sender_is_mod(self, create_users, monkeypatch):
        test_case_note = _make_test_note(recipient="user2", mod_copy='y', staff_note="ThisIsAdditionalStaffInfo")

        monkeypatch.setattr(staff, 'MODS', frozenset([create_users['user1']]))

        note.send(create_users['user1'], test_case_note)

        result = shout.select(userid=create_users['user1'], ownerid=create_users['user2'], staffnotes=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert test_case_note.title in result[0]['content']
        assert test_case_note.content in result[0]['content']
        assert test_case_note.staff_note in result[0]['content']

    @pytest.mark.usefixtures('db')
    def test_update_of_header_info(self, create_users):
        test_case_note = _make_test_note(recipient="user1")
        result = d._page_header_info(create_users['user1'])
        # Currently, we have zero notes
        assert result[0] == 0

        note.send(create_users['user2'], test_case_note)
        result = d._page_header_info(create_users['user1'])
        # user1 now has a single note; ensure the header info updates
        assert result[0] == 1

import pytest

from weasyl import comment, siteupdate
from weasyl.test import db_utils


@pytest.mark.usefixtures('db', 'cache')
def test_created_at_timestamp_consistency(app):
    userid = db_utils.create_user()

    submitid = db_utils.create_submission(userid)
    charid = db_utils.create_character(userid)
    journalid = db_utils.create_journal(userid)
    updateid = siteupdate.create(userid=userid, title='', content='', wesley=False)

    submit_parentid = db_utils.create_submission_comment(userid, submitid)
    char_parentid = db_utils.create_character_comment(userid, charid)
    journal_parentid = db_utils.create_journal_comment(userid, journalid)
    update_parentid, _ = comment.insert(userid, updateid=updateid, parentid=None, content='foo')

    submit_form = {'format': 'json', 'content': 'foo', 'submitid': submitid, 'parentid': submit_parentid}
    char_form = {'format': 'json', 'content': 'foo', 'charid': charid, 'parentid': char_parentid}
    journal_form = {'format': 'json', 'content': 'foo', 'journalid': journalid, 'parentid': journal_parentid}
    update_form = {'format': 'json', 'content': 'foo', 'updateid': updateid, 'parentid': update_parentid}

    headers = {'Cookie': db_utils.create_session(userid)}

    submit_resp = app.post('/submit/comment', submit_form, headers=headers)
    char_resp = app.post('/submit/comment', char_form, headers=headers)
    journal_resp = app.post('/submit/comment', journal_form, headers=headers)
    update_resp = app.post('/submit/comment', update_form, headers=headers)

    created_at_times = list(map(lambda resp: resp.json['createdAt'],
                                (submit_resp, char_resp, journal_resp, update_resp)))

    # Checking for a difference within one minute is arbitrary;
    # we really want to make sure there isn't a UNIXTIME_OFFSET-sized difference
    # while keeping some variance for each reply having a different timestamp.
    assert max(created_at_times) - min(created_at_times) < 60

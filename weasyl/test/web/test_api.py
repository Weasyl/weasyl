# encoding: utf-8
from __future__ import absolute_import, division

import pytest
import webtest

import weasyl.define as d
from weasyl.test.web.common import create_visual, read_asset


@pytest.mark.usefixtures('db', 'no_csrf')
def test_submission_view(app, submission_user):
    submission = create_visual(
        app,
        submission_user,
        submitfile=webtest.Upload('wesley1.png', read_asset('img/wesley1.png'), 'image/png'),
    )
    d.engine.execute('UPDATE submission SET unixtime = 1581092121 WHERE submitid = %(id)s', id=submission)

    resp_json = app.get('/api/submissions/%i/view' % (submission,)).json
    media = resp_json.pop('media', None)
    owner_media = resp_json.pop('owner_media', None)

    assert resp_json == {
        'comments': 0,
        'description': '<p>Description</p>',
        'embedlink': None,
        'favorited': False,
        'favorites': 0,
        'folderid': None,
        'folder_name': None,
        'friends_only': False,
        'link': 'http://localhost/submission/%i/test-title' % (submission,),
        'owner': 'submission_test',
        'owner_login': 'submissiontest',
        'posted_at': '2020-02-07T21:15:21+00:00Z',
        'rating': 'general',
        'submitid': submission,
        'subtype': 'visual',
        'tags': ['bar', 'foo'],
        'title': 'Test title',
        'type': 'submission',
        'views': 1,
    }
    assert set(media) == {'thumbnail', 'submission', 'cover', 'thumbnail-generated-webp', 'thumbnail-generated'}
    assert type(media['submission'][0].pop('mediaid')) is int
    assert set(media['submission'][0].pop('links')) == {'cover'}
    assert media['submission'] == [{
        'url': 'http://localhost/~submissiontest/submissions/%i/ca23760d8ca4bf6c2d721f5b02e389627b6b9181d5f323001f2d5801c086407b/submissiontest-test-title.png' % (submission,),
    }]
    assert owner_media == {
        'avatar': [{
            'mediaid': None,
            'url': 'http://localhost/img/default-avatar-vuOx5v6OBn.jpg',
        }],
    }


@pytest.mark.usefixtures('db')
def test_submission_view_missing(app):
    resp = app.get('/api/submissions/1/view', status=404)
    assert resp.json == {'error': {'name': 'submissionRecordMissing'}}

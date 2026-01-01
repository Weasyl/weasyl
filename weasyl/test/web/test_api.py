import pytest
import webtest

import weasyl.define as d
from weasyl.test import db_utils
from weasyl.test.web.common import create_visual, read_asset


@pytest.mark.usefixtures('db')
def test_submission_views(app, submission_user, subtests: pytest.Subtests) -> None:
    submission = create_visual(
        app,
        submission_user,
        submitfile=webtest.Upload('wesley1.png', read_asset('img/wesley1.png'), 'image/png'),
    )
    d.engine.execute('UPDATE submission SET unixtime = 1581092121 WHERE submitid = %(id)s', id=submission)

    with subtests.test("submission view"):
        resp_json = app.get('/api/submissions/%i/view' % (submission,)).json
        media = resp_json.pop('media', None)
        owner_media = resp_json.pop('owner_media', None)

        assert resp_json == {
            'comments': 0,
            'description': '<p>Description</p>\n',
            'embedlink': None,
            'favorited': False,
            'favorites': 0,
            'folderid': None,
            'folder_name': None,
            'friends_only': False,
            'link': 'http://localhost/submission/%i/test-title' % (submission,),
            'owner': 'submission_test',
            'owner_login': 'submissiontest',
            'posted_at': '2020-02-07T21:15:21Z',
            'rating': 'general',
            'submitid': submission,
            'subtype': 'visual',
            'tags': ['bar', 'foo'],
            'title': 'Test title',
            'type': 'submission',
            'views': 0,
        }
        assert set(media) == {'thumbnail', 'submission', 'cover', 'thumbnail-generated-webp', 'thumbnail-generated'}
        assert type(media['submission'][0].pop('mediaid')) is int
        assert media['submission'] == [{
            'url': 'http://localhost/~submissiontest/submissions/%i/ca23760d8ca4bf6c2d721f5b02e389627b6b9181d5f323001f2d5801c086407b/submissiontest-test-title.png' % (submission,),
        }]
        assert owner_media == {
            'avatar': [{
                'mediaid': None,
                'url': 'http://localhost/img/default-avatar-vuOx5v6OBn.jpg',
            }],
        }

        with subtests.test("with favorite"):
            favoriter = db_utils.create_user()
            db_utils.create_favorite(favoriter, submitid=submission)

            resp_json = app.get('/api/submissions/%i/view' % (submission,)).json
            assert resp_json['favorites'] == 1

    with subtests.test("frontpage"):
        frontpage_json = app.get('/api/submissions/frontpage').json

        expected_media = resp_json['media']
        del expected_media['cover']
        del expected_media['submission']

        assert frontpage_json == [{
            'link': 'http://localhost/submission/%i/test-title' % (submission,),
            'owner': 'submission_test',
            'owner_login': 'submissiontest',
            'posted_at': '2020-02-07T21:15:21Z',
            'rating': 'general',
            'submitid': submission,
            'subtype': 'visual',
            'tags': ['bar', 'foo'],
            'title': 'Test title',
            'type': 'submission',
            'media': expected_media,
        }]


@pytest.mark.usefixtures('db')
def test_submission_view_missing(app):
    resp = app.get('/api/submissions/1/view', status=404)
    assert resp.json == {'error': {'name': 'submissionRecordMissing'}}


@pytest.mark.usefixtures('db', 'cache')
def test_useravatar(app, submission_user):
    resp = app.get('/api/useravatar?username=submissiontest')
    assert resp.json == {
        'avatar': 'http://localhost/img/default-avatar-vuOx5v6OBn.jpg',
    }


@pytest.mark.usefixtures('db', 'cache')
def test_useravatar_missing(app, submission_user):
    resp = app.get('/api/useravatar?username=foo', status=404)
    assert resp.json == {'error': {'name': 'userRecordMissing'}}


@pytest.mark.usefixtures('db', 'cache')
def test_user_view(app, submission_user):
    resp = app.get('/api/users/submissiontest/view')
    assert resp.json == {
        'banned': False,
        'catchphrase': '',
        'commission_info': {
            'commissions': 'closed',
            'requests': 'closed',
            'trades': 'closed',
            'details': '',
            'price_classes': None,
        },
        'created_at': '1970-01-01T00:00:00Z',
        'featured_submission': None,
        'folders': [],
        'full_name': 'submission_test',
        'link': 'http://localhost/~submissiontest',
        'login_name': 'submissiontest',
        'media': {
            'avatar': [{
                'mediaid': None,
                'url': 'http://localhost/img/default-avatar-vuOx5v6OBn.jpg',
            }],
        },
        'profile_text': '',
        'recent_submissions': [],
        'recent_type': 'submissions',
        'relationship': None,
        'show_favorites_bar': True,
        'show_favorites_tab': True,
        'statistics': {
            'faves_received': 0,
            'faves_sent': 0,
            'followed': 0,
            'following': 0,
            'journals': 0,
            'page_views': 0,
            'submissions': 0,
        },
        'stream_text': None,
        'stream_url': '',
        'streaming_status': 'stopped',
        'suspended': False,
        'user_info': {
            'age': None,
            'gender': '',
            'location': '',
            'sorted_user_links': [],
            'user_links': {},
        },
        'username': 'submission_test',
    }


@pytest.mark.usefixtures('db', 'cache')
def test_user_view_missing(app):
    resp = app.get('/api/users/foo/view', status=404)
    assert resp.json == {'error': {'name': 'userRecordMissing'}}


@pytest.mark.usefixtures('db', 'cache')
def test_user_view_unverified(app):
    db_utils.create_user(username='unverified_test', verified=False)
    resp = app.get('/api/users/unverifiedtest/view', status=403)
    assert resp.json == {
        'error': {
            'code': 201,
            'text': 'Unverified accounts are hidden to reduce spam.',
        },
    }


@pytest.mark.usefixtures('db', 'cache')
def test_user_view_no_guests(app):
    db_utils.create_user(
        username='private_test',
        profile_guests=False,
    )
    resp = app.get('/api/users/privatetest/view', status=403)
    assert resp.json == {
        'error': {
            'code': 200,
            'text': 'Profile hidden from guests.',
        },
    }


@pytest.mark.usefixtures('db', 'cache')
def test_whoami_unauthenticated(app):
    resp = app.get('/api/whoami', status=401)
    assert resp.json == {'error': {'code': 110, 'text': 'Session unsigned'}}

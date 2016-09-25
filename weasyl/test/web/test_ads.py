from __future__ import absolute_import, unicode_literals

import datetime
import pytest
import web
import webtest

from libweasyl import staff
from weasyl import ads
from weasyl import errorcode
from weasyl.test import db_utils
from weasyl.test.web.wsgi import app


EARLIER = datetime.datetime.now() - datetime.timedelta(seconds=1)
LATER = datetime.datetime.now() + datetime.timedelta(days=28)

CORRECT_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01,\x00\x00\x00d\x01\x00\x00\x00\x00\x14z0m\x00\x00\x00\x1bIDATx\xda\xed\xc1\x81\x00\x00\x00\x00\xc3\xa0\xf9S\xdf\xe0\x04U\x01\x00\x00\x00\xcf\x00\x0f<\x00\x013Szy\x00\x00\x00\x00IEND\xaeB`\x82'
CORRECT_JPEG = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x00\x0b\x08\x00d\x01,\x01\x01\x11\x00\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x98\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xd9'
CORRECT_GIF = b'GIF89a,\x01d\x00\xf0\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00!\xff\x0bImageMagick\x0egamma=0.454545\x00,\x00\x00\x00\x00,\x01d\x00\x00\x02\xdb\x84\x8f\xa9\xcb\xed\x0f\xa3\x9c\xb4\xda\x8b\xb3\xde\xbc\xfb\x0f\x86\xe2H\x96\xe6\x89\xa6\xea\xca\xb6\xee\x0b\xc7\xf2L\xd7\xf6\x8d\xe7\xfa\xce\xf7\xfe\x0f\x0c\n\x87\xc4\xa2\xf1\x88L*\x97\xcc\xa6\xf3\t\x8dJ\xa7\xd4\xaa\xf5\x8a\xcdj\xb7\xdc\xae\xf7\x0b\x0e\x8b\xc7\xe4\xb2\xf9\x8cN\xab\xd7\xec\xb6\xfb\r\x8f\xcb\xe7\xf4\xba\xfd\x8e\xcf\xeb\xf7\xfc\xbe\xff\x0f\x18(8HXhx\x88\x98\xa8\xb8\xc8\xd8\xe8\xf8\x08\x19)9IYiy\x89\x99\xa9\xb9\xc9\xd9\xe9\xf9\t\x1a*:JZjz\x8a\x9a\xaa\xba\xca\xda\xea\xfa\n\x1b+;K[k{\x8b\x9b\xab\xbb\xcb\xdb\xeb\xfb\x0b\x1c,<L\\l|\x8c\x9c\xac\xbc\xcc\xdc\xec\xfc\x0c\x1d-=M]m}\x8d\x9d\xad\xbd\xcd\xdd\xed\xfd\r\x1e.>N^n~\x8e\x9e\xae\xbe\xce\xde\xee\xfe\x0e\x1f/?O_o\x7f\x8f/W\x00\x00;'
CORRECT_WEBP = b'RIFFr\x00\x00\x00WEBPVP8 f\x00\x00\x00P\n\x00\x9d\x01*,\x01d\x00>\x91H\xa1M%\xa4#" H\x00\xb0\x12\tin\xe1v\xb1\x1b@\x13\xda\xf4U\xc2\x0c\x82\x1a\xaaMv\xda.\x10d\x10\xd5Rk\xb6\xd1p\x83 \x86\xaa\x93]\xb6\x8b\x84\x19\x045T\x9a\xed\xb4\\ \xc8!\xaa\xa4\xd7m\xa2\xe1\x06A\rU&\xbbm\x17\x08/@\x00\xfe\xff\xbc\x11m\x80\x00\x00\x00\x00'

INCORRECT_DIMENSIONS_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01-\x00\x00\x00d\x01\x00\x00\x00\x00\xfb\xb8[S\x00\x00\x00\x1bIDATx\xda\xed\xc1\x81\x00\x00\x00\x00\xc3\xa0\xf9S\xdf\xe0\x04U\x01\x00\x00\x00\xcf\x00\x0f<\x00\x013Szy\x00\x00\x00\x00IEND\xaeB`\x82'


def get_image_form(image):
    return {
        'target': 'https://example.com/',
        'image': webtest.Upload('ad', image),
        'owner': 'test@weasyl.com',
        'end': LATER.strftime('%Y-%m-%d'),
    }


CORRECT_PNG_FORM = get_image_form(CORRECT_PNG)
MISSING_IMAGE_FORM = get_image_form(b'')
OVERSIZE_PNG_FORM = get_image_form(CORRECT_PNG + b'\0' * ads.SIZE_LIMIT)
INCORRECT_DIMENSIONS_PNG_FORM = get_image_form(INCORRECT_DIMENSIONS_PNG)

INVALID_TARGET_FORM = dict(CORRECT_PNG_FORM, target='javascript://example.com/')
INVALID_END_DATE_FORM = dict(CORRECT_PNG_FORM, end='01/02/2016')

CORRECT_PNG_STORAGE = web.Storage(
    target='https://example.com/',
    image=CORRECT_PNG,
    owner='test@weasyl.com',
    end=LATER,
)

EXPIRED_PNG_STORAGE = web.Storage(
    target='https://example.com/',
    image=CORRECT_PNG,
    owner='test@weasyl.com',
    end=EARLIER,
)


@pytest.mark.usefixtures('db', 'cache')
def test_current_none():
    assert ads.get_current_ads() == []


@pytest.mark.usefixtures('db', 'cache')
def test_current_some():
    ads.create_ad(CORRECT_PNG_STORAGE)
    current = ads.get_current_ads()
    assert len(current) == 1
    assert current[0].link_target == 'https://example.com/'


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', CORRECT_PNG_FORM, headers={'Cookie': cookie})
    assert resp.html.find(None, 'created') is not None


@pytest.mark.usefixtures('db', 'cache')
def test_upload_csrf(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', CORRECT_PNG_FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.token


@pytest.mark.usefixtures('db', 'cache')
def test_upload_restricted(monkeypatch):
    resp = app.get('/ads/create')
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned
    resp = app.post('/ads/create', CORRECT_PNG_FORM)
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/ads/create', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/ads/create', CORRECT_PNG_FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([user]))
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))
    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.get('/ads/create', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission
    resp = app.post('/ads/create', CORRECT_PNG_FORM, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission

    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.get('/ads/create', headers={'Cookie': cookie})
    assert resp.html.find(id='error_content') is None


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload_file_required(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', MISSING_IMAGE_FORM, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adImageMissing']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload_filesize_limit(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', OVERSIZE_PNG_FORM, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adImageSizeInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload_dimensions(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', INCORRECT_DIMENSIONS_PNG_FORM, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adImageDimensionsInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload_types(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', get_image_form(CORRECT_JPEG), headers={'Cookie': cookie})
    assert resp.html.find(None, 'created') is not None
    resp = app.post('/ads/create', get_image_form(CORRECT_GIF), headers={'Cookie': cookie})
    assert resp.html.find(None, 'created') is not None

    resp = app.post('/ads/create', get_image_form(CORRECT_WEBP), headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adImageTypeInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_upload_target(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', INVALID_TARGET_FORM, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adTargetInvalid']


@pytest.mark.usefixtures('db', 'no_csrf')
def test_end_date_format(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads/create', INVALID_END_DATE_FORM, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.string == errorcode.error_messages['adEndDateInvalid']


@pytest.mark.usefixtures('db', 'cache')
def test_expiry(monkeypatch):
    ads.create_ad(EXPIRED_PNG_STORAGE)
    resp = app.get('/ads')
    assert resp.html.find(id='ad-list') is None


@pytest.mark.usefixtures('db', 'no_csrf')
def test_takedown(monkeypatch):
    ad_id = ads.create_ad(CORRECT_PNG_STORAGE)

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    app.post('/ads', {'takedown': u'%d' % (ad_id,)}, headers={'Cookie': cookie})
    assert ads.get_current_ads() == []


@pytest.mark.usefixtures('db', 'cache')
def test_takedown_csrf(monkeypatch):
    ad_id = ads.create_ad(CORRECT_PNG_STORAGE)

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    resp = app.post('/ads', {'takedown': u'%d' % (ad_id,)}, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.token


@pytest.mark.usefixtures('db', 'no_csrf')
def test_takedown_restricted(monkeypatch):
    ad_id = ads.create_ad(CORRECT_PNG_STORAGE)

    resp = app.post('/ads', {'takedown': u'%d' % (ad_id,)})
    assert resp.html.find(id='error_content').contents[0].strip() == errorcode.unsigned

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    monkeypatch.setattr(staff, 'TECHNICAL', frozenset([user]))
    monkeypatch.setattr(staff, 'ADMINS', frozenset([user]))
    monkeypatch.setattr(staff, 'MODS', frozenset([user]))

    resp = app.post('/ads', {'takedown': u'%d' % (ad_id,)}, headers={'Cookie': cookie})
    assert resp.html.find(id='error_content').p.string == errorcode.permission


@pytest.mark.usefixtures('db', 'cache')
def test_empty_list():
    resp = app.get('/ads')
    assert resp.html.find(id='ads-content').p.string == 'No current advertisements.'
    assert resp.html.find(None, 'ad-list') is None


@pytest.mark.usefixtures('db', 'cache')
def test_nonempty_list():
    ads.create_ad(CORRECT_PNG_STORAGE)
    ads.create_ad(CORRECT_PNG_STORAGE)
    resp = app.get('/ads')
    assert len(resp.html.find(id='ad-list').findAll(None, 'ad-detail')) == 2
    assert resp.html.find(None, 'ad-detail-takedown') is None


@pytest.mark.usefixtures('db', 'cache')
def test_list_takedown(monkeypatch):
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)
    monkeypatch.setattr(staff, 'DIRECTORS', frozenset([user]))

    ads.create_ad(CORRECT_PNG_STORAGE)
    resp = app.get('/ads', headers={'Cookie': cookie})
    assert resp.html.find(None, 'ad-detail-takedown') is not None


@pytest.mark.usefixtures('db', 'cache')
def test_no_displayed_ads():
    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/')
    assert resp.html.find(id='home-ads') is None

    resp = app.get('/messages/notifications', headers={'Cookie': cookie})
    assert resp.html.find(id='notification-ads') is None

    resp = app.get('/messages/submissions', headers={'Cookie': cookie})
    assert resp.html.find(id='notification-ads') is None


@pytest.mark.usefixtures('db', 'cache')
def test_displayed_ads():
    ads.create_ad(CORRECT_PNG_STORAGE)
    ads.create_ad(CORRECT_PNG_STORAGE)

    user = db_utils.create_user()
    cookie = db_utils.create_session(user)

    resp = app.get('/')
    assert len(resp.html.findAll(None, 'ad-multiple')) == 2

    resp = app.get('/messages/notifications', headers={'Cookie': cookie})
    assert len(resp.html.findAll(None, 'ad-multiple')) == 2

    resp = app.get('/messages/submissions', headers={'Cookie': cookie})
    assert len(resp.html.findAll(None, 'ad-multiple')) == 2

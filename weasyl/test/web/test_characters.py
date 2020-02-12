# encoding: utf-8
from __future__ import absolute_import

import os
import pytest
import webtest
from PIL import Image

from weasyl.macro import MACRO_STORAGE_ROOT
from weasyl.test import db_utils
from weasyl.test.web.common import read_asset, read_asset_image


_BASE_FORM = {
    'title': u'Test name',
    'age': u'64021610030',
    'gender': u'🦊',
    'height': u'Test height',
    'weight': u'Test weight',
    'species': u'Test species',
    'rating': '10',
    'content': u'Description',
    'tags': u'',
}


def _read_character_image(image_url):
    parts = image_url.split('/')[1:]
    parts[-1] = parts[-1].split('-', 1)[1]
    full_path = os.path.join(MACRO_STORAGE_ROOT, *parts)
    return Image.open(full_path).convert('RGBA')


@pytest.fixture(name='character_user')
def _character_user(db):
    return db_utils.create_user(username='character_test')


@pytest.fixture(name='character')
def _character(app, db, character_user, no_csrf):
    cookie = db_utils.create_session(character_user)

    form = dict(
        _BASE_FORM,
        submitfile=webtest.Upload('wesley', read_asset('img/wesley1.png'), 'image/png'),
    )

    resp = app.post('/submit/character', form, headers={'Cookie': cookie}).follow(headers={'Cookie': cookie})
    charid = int(resp.html.find('input', {'name': 'charid'})['value'])

    return charid


@pytest.mark.usefixtures('db', 'character_user')
def test_list_empty(app):
    resp = app.get('/characters/character_test')
    assert list(resp.html.find(class_='user-characters').stripped_strings) == [u'Characters', u'There are no characters to display.']


@pytest.mark.usefixtures('db', 'character')
def test_create_default_thumbnail(app, character):
    resp = app.get('/character/%d/test-name' % (character,))
    assert resp.html.find(id='detail-bar-title').string == u'Test name'
    assert resp.html.find(id='char-stats').find('dt', text=u'Gender:').findNext('dd').string == u'🦊'

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == read_asset_image('img/wesley1.png').tobytes()


@pytest.mark.usefixtures('db', 'character_user', 'character', 'no_csrf')
def test_owner_edit_details(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    form = dict(
        _BASE_FORM,
        charid=str(character),
        title=u'Edited name',
    )

    resp = app.post('/edit/character', form, headers={'Cookie': cookie}).follow()
    assert resp.html.find(id='detail-bar-title').string == u'Edited name'


@pytest.mark.usefixtures('db', 'character_user', 'character', 'no_csrf')
def test_owner_reupload(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    resp = app.post('/reupload/character', {
        'targetid': str(character),
        'submitfile': webtest.Upload('wesley', read_asset('img/help/wesley-draw.png'), 'image/png'),
    }, headers={'Cookie': cookie}).follow()

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == read_asset_image('img/help/wesley-draw.png').tobytes()

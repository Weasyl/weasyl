# encoding: utf-8


import os
import pytest
import webtest
from io import BytesIO
from PIL import Image

from weasyl.macro import MACRO_APP_ROOT, MACRO_STORAGE_ROOT
from weasyl.test import db_utils


_BASE_FORM = {
    'title': 'Test name',
    'age': '64021610030',
    'gender': '🦊',
    'height': 'Test height',
    'weight': 'Test weight',
    'species': 'Test species',
    'rating': '10',
    'content': 'Description',
    'tags': '',
}


_static_cache = {}


def _static(path):
    full_path = os.path.join(MACRO_APP_ROOT, 'static', path)

    if full_path not in _static_cache:
        with open(full_path, 'rb') as f:
            _static_cache[full_path] = f.read()

    return _static_cache[full_path]


def _read_character_image(image_url):
    parts = image_url.split('/')[1:]
    parts[-1] = parts[-1].split('-', 1)[1]
    full_path = os.path.join(MACRO_STORAGE_ROOT, *parts)
    return Image.open(full_path).convert('RGBA')


def _read_static_image(path):
    return Image.open(BytesIO(_static(path))).convert('RGBA')


@pytest.fixture(name='character_user')
def _character_user(db):
    return db_utils.create_user(username='character_test')


@pytest.fixture(name='character')
def _character(app, db, character_user, no_csrf):
    cookie = db_utils.create_session(character_user)

    form = dict(
        _BASE_FORM,
        submitfile=webtest.Upload('wesley', _static('images/wesley1.png'), 'image/png'),
    )

    resp = app.post('/submit/character', form, headers={'Cookie': cookie}).follow(headers={'Cookie': cookie})
    charid = int(resp.html.find('input', {'name': 'charid'})['value'])

    return charid


@pytest.mark.usefixtures('db', 'character_user')
def test_list_empty(app):
    resp = app.get('/characters/character_test')
    assert list(resp.html.find(class_='user-characters').stripped_strings) == ['Characters', 'There are no characters to display.']


@pytest.mark.usefixtures('db', 'character')
def test_create_default_thumbnail(app, character):
    resp = app.get('/character/%d/test-name' % (character,))
    assert resp.html.find(id='detail-bar-title').string == 'Test name'
    assert resp.html.find(id='char-stats').find('dt', text='Gender:').findNext('dd').string == '🦊'

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == _read_static_image('images/wesley1.png').tobytes()


@pytest.mark.usefixtures('db', 'character_user', 'character', 'no_csrf')
def test_owner_edit_details(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    form = dict(
        _BASE_FORM,
        charid=str(character),
        title='Edited name',
    )

    resp = app.post('/edit/character', form, headers={'Cookie': cookie}).follow()
    assert resp.html.find(id='detail-bar-title').string == 'Edited name'


@pytest.mark.usefixtures('db', 'character_user', 'character', 'no_csrf')
def test_owner_reupload(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    resp = app.post('/reupload/character', {
        'targetid': str(character),
        'submitfile': webtest.Upload('wesley', _static('images/wesley-draw.png'), 'image/png'),
    }, headers={'Cookie': cookie}).follow()

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == _read_static_image('images/wesley-draw.png').tobytes()

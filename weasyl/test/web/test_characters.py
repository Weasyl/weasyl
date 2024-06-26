import os
import pytest
import webtest
from PIL import Image

from weasyl.macro import MACRO_STORAGE_ROOT
from weasyl.test import db_utils
from weasyl.test.web.common import read_asset, read_asset_image


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


def _read_character_image(image_url):
    parts = image_url.split('/')[1:]
    parts[-1] = parts[-1].split('-', 1)[1]
    full_path = os.path.join(MACRO_STORAGE_ROOT, *parts)
    return Image.open(full_path).convert('RGBA')


@pytest.fixture(name='character_user')
def _character_user(db):
    return db_utils.create_user(username='character_test')


def create_character(app, character_user, **kwargs):
    cookie = db_utils.create_session(character_user)

    for field in kwargs.keys():
        if field not in _BASE_FORM:
            raise KeyError(field)

    form = {
        **_BASE_FORM,
        "submitfile": webtest.Upload('wesley', read_asset('img/wesley1.png'), 'image/png'),
        **kwargs,
    }

    resp = app.post('/submit/character', form, headers={'Cookie': cookie}).follow(headers={'Cookie': cookie})
    charid = int(resp.html.find('input', {'name': 'charid'})['value'])

    return charid


@pytest.fixture(name='character')
def _character(app, db, character_user):
    return create_character(app, character_user)


@pytest.mark.usefixtures('db', 'character_user')
def test_list_empty(app):
    resp = app.get('/characters/character_test')
    assert list(resp.html.find(class_='user-characters').stripped_strings) == ['Characters', 'There are no characters to display.']


@pytest.mark.usefixtures('db', 'character')
def test_create_default_thumbnail(app, character):
    resp = app.get('/character/%d/test-name' % (character,))
    assert resp.html.find(id='detail-bar-title').string == 'Test name'
    assert resp.html.find(id='char-stats').find('dt', string='Gender:').findNext('dd').string == '🦊'

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == read_asset_image('img/wesley1.png').tobytes()


@pytest.mark.usefixtures('db', 'character_user', 'character')
def test_owner_edit_details(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    form = dict(
        _BASE_FORM,
        charid=str(character),
        title='Edited name',
    )

    resp = app.post('/edit/character', form, headers={'Cookie': cookie}).follow()
    assert resp.html.find(id='detail-bar-title').string == 'Edited name'


@pytest.mark.usefixtures('db', 'character_user', 'character')
def test_owner_reupload(app, character_user, character):
    cookie = db_utils.create_session(character_user)

    resp = app.post('/reupload/character', {
        'targetid': str(character),
        'submitfile': webtest.Upload('wesley', read_asset('img/help/wesley-draw.png'), 'image/png'),
    }, headers={'Cookie': cookie}).follow()

    image_url = resp.html.find(id='detail-art').a['href']
    assert _read_character_image(image_url).tobytes() == read_asset_image('img/help/wesley-draw.png').tobytes()

import os
from io import BytesIO

from PIL import Image

from weasyl.macro import MACRO_APP_ROOT, MACRO_STORAGE_ROOT
from weasyl.test import db_utils


_asset_cache = {}


def read_asset(path):
    full_path = os.path.join(MACRO_APP_ROOT, 'assets', path)

    if full_path not in _asset_cache:
        with open(full_path, 'rb') as f:
            _asset_cache[full_path] = f.read()

    return _asset_cache[full_path]


def read_asset_image(path):
    return Image.open(BytesIO(read_asset(path))).convert('RGBA')


def get_storage_path(url):
    return os.path.join(MACRO_STORAGE_ROOT, url[1:])


def read_storage_image(image_url):
    full_path = get_storage_path(image_url)
    return Image.open(full_path).convert('RGBA')


BASE_VISUAL_FORM = {
    'submitfile': '',
    'thumbfile': '',
    'title': 'Test title',
    'subtype': '1030',
    'folderid': '',
    'rating': '10',
    'content': 'Description',
    'tags': 'foo bar ',
}

BASE_LITERARY_FORM = {
    'submitfile': '',
    'embedlink': '',
    'coverfile': '',
    'thumbfile': '',
    'title': 'Test title',
    'subtype': '2010',
    'folderid': '',
    'rating': '10',
    'content': 'Description',
    'tags': 'foo bar',
}


def create_visual(app, user, **kwargs):
    cookie = db_utils.create_session(user)
    form = dict(BASE_VISUAL_FORM, **kwargs)
    resp = app.post('/submit/visual', form, headers={'Cookie': cookie}).maybe_follow(headers={'Cookie': cookie})
    submitid = int(resp.html.find('input', {'name': 'submitid'})['value'])

    return submitid

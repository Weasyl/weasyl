# encoding: utf-8
from __future__ import absolute_import, division

import os
from io import BytesIO

from PIL import Image

from weasyl.macro import MACRO_APP_ROOT, MACRO_STORAGE_ROOT
from weasyl.test import db_utils


_static_cache = {}


def read_static(path):
    full_path = os.path.join(MACRO_APP_ROOT, 'static', path)

    if full_path not in _static_cache:
        with open(full_path, 'rb') as f:
            _static_cache[full_path] = f.read()

    return _static_cache[full_path]


def read_static_image(path):
    return Image.open(BytesIO(read_static(path))).convert('RGBA')


def read_storage_image(image_url):
    full_path = os.path.join(MACRO_STORAGE_ROOT, image_url[1:])
    return Image.open(full_path).convert('RGBA')


_BASE_VISUAL_FORM = {
    'submitfile': u'',
    'thumbfile': u'',
    'title': u'Test title',
    'subtype': u'1030',
    'folderid': u'',
    'rating': u'10',
    'content': u'Description',
    'tags': u'foo bar ',
}


def create_visual(app, user, **kwargs):
    cookie = db_utils.create_session(user)
    form = dict(_BASE_VISUAL_FORM, **kwargs)
    resp = app.post('/submit/visual', form, headers={'Cookie': cookie}).maybe_follow(headers={'Cookie': cookie})
    submitid = int(resp.html.find('input', {'name': 'submitid'})['value'])

    return submitid

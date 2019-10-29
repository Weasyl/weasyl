# encoding: utf-8
from __future__ import absolute_import, division

import os
from io import BytesIO

from PIL import Image

from weasyl.macro import MACRO_APP_ROOT, MACRO_STORAGE_ROOT


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

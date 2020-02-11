from __future__ import unicode_literals

import pytest

from PIL import Image

from libweasyl.test.common import datadir
from libweasyl import images


def test_image_load_file():
    image_file = datadir.join('1200x6566.png')
    image = images.WeasylImage(fp=str(image_file))
    assert image.size == (1200, 6566)
    assert image.file_format == "png"
    assert image.image_extension == ".png"
    assert image.attributes == {'width': 1200, 'height': 6566}


def test_image_load_string():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (1200, 6566)
    assert image.file_format == "png"
    assert image.image_extension == ".png"
    assert image.attributes == {'width': 1200, 'height': 6566}


def test_image_save_file(tmpdir):
    image_file = datadir.join('1200x6566.png')
    image = images.WeasylImage(fp=str(image_file))
    save_file = tmpdir.join('1200x6566.png')
    image.save(str(save_file))
    assert save_file.ensure()


def test_image_save_string():
    image_file = datadir.join('1200x6566.png')
    image = images.WeasylImage(fp=str(image_file))
    out = image.to_buffer()
    assert out is not None


def test_image_resize():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (1200, 6566)
    assert image.attributes == {'width': 1200, 'height': 6566}
    image.resize((200, 200))
    assert image.size == (200, 200)
    assert image.attributes == {'width': 200, 'height': 200}


def test_image_crop():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (1200, 6566)
    assert image.attributes == {'width': 1200, 'height': 6566}
    image.crop((100, 100, 200, 200))
    assert image.size == (100, 100)
    assert image.attributes == {'width': 100, 'height': 100}


def test_image_shrinkcrop_size():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (1200, 6566)
    assert image.attributes == {'width': 1200, 'height': 6566}
    image.shrinkcrop((100, 100))
    assert image.size == (100, 100)
    assert image.attributes == {'width': 100, 'height': 100}


def test_image_shrinkcrop_bounds():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (1200, 6566)
    assert image.attributes == {'width': 1200, 'height': 6566}
    image.shrinkcrop((100, 100), (200, 200, 400, 400))
    assert image.size == (100, 100)
    assert image.attributes == {'width': 100, 'height': 100}


def test_image_gif_load_file():
    image_file = datadir.join('100x100_2_frames.gif')
    image = images.WeasylImage(fp=str(image_file))
    assert image.size == (100, 100)
    assert image.attributes == {'width': 100, 'height': 100}
    assert image.file_format == "gif"
    assert image.image_extension == ".gif"
    assert image.is_animated is True
    assert image.frames == 2


def test_image_gif_load_string():
    image_file = datadir.join('100x100_2_frames.gif').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    assert image.size == (100, 100)
    assert image.attributes == {'width': 100, 'height': 100}
    assert image.file_format == "gif"
    assert image.image_extension == ".gif"
    assert image.is_animated is True
    assert image.frames == 2


def test_image_gif_save_file(tmpdir):
    image_file = datadir.join('100x100_2_frames.gif')
    image = images.WeasylImage(fp=str(image_file))
    save_file = tmpdir.join('100x1000_2_frames.gif')
    image.save(str(save_file))
    assert save_file.ensure()
    image_verify = Image.open(str(save_file))
    image_verify.seek(1)
    assert image_verify.tell() == 1
    with pytest.raises(EOFError):
        image_verify.seek(2)


def test_image_get_thumbnail():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    image.get_thumbnail()
    assert image.size[1] <= 250


def test_image_get_thumbnail_bounds():
    image_file = datadir.join('1200x6566.png').read(mode='rb')
    image = images.WeasylImage(string=image_file)
    image.get_thumbnail(bounds=(200, 200, 500, 500))
    assert image.size[1] <= 250

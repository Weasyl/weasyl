from __future__ import absolute_import

import logging
import os

from sanpera.exception import SanperaError
from sanpera.image import Image
from sanpera import geometry

from libweasyl import images
from weasyl import files
from weasyl.define import log_exc
from weasyl.error import WeasylError


COVER_SIZE = 1024, 3000


def read(filename):
    try:
        return Image.read(filename)
    except SanperaError:
        log_exc(level=logging.DEBUG)
        raise WeasylError('imageDecodeError')


def from_string(filedata):
    try:
        return Image.from_buffer(filedata)
    except SanperaError:
        log_exc(level=logging.DEBUG)
        raise WeasylError('imageDecodeError')


def image_setting(im):
    if im.original_format in (b'JPG', b'JPEG'):
        return 'J'
    if im.original_format == b'PNG':
        return 'P'
    if im.original_format == b'GIF':
        return 'G'


def check_crop(dim, x1, y1, x2, y2):
    """
    Return True if the specified crop coordinates are valid, else False.
    """
    return (
        x1 >= 0 and y1 >= 0 and x2 >= 0 and y2 >= 0 and x1 <= dim[0] and
        y1 <= dim[1] and x2 <= dim[0] and y2 <= dim[1] and x2 > x1 and y2 > y1)


def check_type(filename):
    """
    Return True if the filename corresponds to an image file, else False.
    """
    try:
        im = Image.read(filename)
    except SanperaError:
        return False
    else:
        return im.original_format in ['JPEG', 'PNG', 'GIF']


def _resize(filename, width, height, destination=None):
    in_place = False
    if not destination:
        destination = filename + '.new'
        in_place = True

    im = read(filename)
    if not images.image_extension(im):
        raise WeasylError("FileType")

    im = images.resize_image(im, width, height)
    if im is not None:
        im.write(destination)
        if in_place:
            os.rename(destination, filename)

    # if there's no need to resize, in-place resize is a no-op. otherwise copy
    # the source to the destination.
    elif not in_place:
        files.copy(filename, destination)


def make_cover(filename, destination=None):
    """
    Create a cover image file; if `destination` is passed, a new file will be
    created and the original left unaltered, else the original file will be
    altered.
    """
    _resize(filename, *COVER_SIZE, destination=destination)


def _shrinkcrop(im, size, bounds=None):
    if bounds is not None:
        ret = im
        if bounds.position != geometry.origin or bounds.size != ret.size:
            ret = ret.cropped(bounds)
        if ret.size != size:
            ret = ret.resized(size)
        return ret
    elif im.size == size:
        return im
    shrunk_size = im.size.fit_around(size)
    shrunk = im
    if shrunk.size != shrunk_size:
        shrunk = shrunk.resized(shrunk_size)
    x1 = (shrunk.size.width - size.width) // 2
    y1 = (shrunk.size.height - size.height) // 2
    bounds = geometry.Rectangle(x1, y1, x1 + size.width, y1 + size.height)
    return shrunk.cropped(bounds)


def shrinkcrop(im, size, bounds=None):
    ret = images.correct_image_and_call(_shrinkcrop, im, size, bounds)
    if ret.size != size or (len(ret) == 1 and ret[0].size != size):
        ignored_sizes = ret.size, ret[0].size  # to log these locals
        raise WeasylError('thumbnailingMessedUp')
        ignored_sizes  # to shut pyflakes up
    return ret

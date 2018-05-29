from __future__ import absolute_import

import logging
import os

from sanpera.exception import SanperaError
from sanpera.image import Image
from sanpera import geometry

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


def image_extension(im):
    if im.original_format in ('JPG', 'JPEG'):
        return '.jpg'
    if im.original_format == 'PNG':
        return '.png'
    if im.original_format == 'GIF':
        return '.gif'


def image_setting(im):
    if im.original_format in ('JPG', 'JPEG'):
        return 'J'
    if im.original_format == 'PNG':
        return 'P'
    if im.original_format == 'GIF':
        return 'G'


def image_file_type(im):
    ret = image_extension(im)
    if ret is not None:
        ret = ret.lstrip('.')
    return ret


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


def _resize(im, width, height):
    """
    Resizes the image to fit within the specified height and width; aspect ratio
    is preserved. Images always preserve animation and might even result in a
    better-optimized animated gif.
    """
    # resize only if we need to; return None if we don't
    if im.size.width > width or im.size.height > height:
        im = im.resized(im.size.fit_inside((width, height)))
        return im


def resize(filename, width, height, destination=None, animate=False):
    in_place = False
    if not destination:
        destination = filename + '.new'
        in_place = True

    im = read(filename)
    if not image_extension(im):
        raise WeasylError("FileType")

    files.ensure_file_directory(filename)
    im = correct_image_and_call(_resize, im, width, height)
    if im is not None:
        im.write(destination)
        if in_place:
            os.rename(destination, filename)

    # if there's no need to resize, in-place resize is a no-op. otherwise copy
    # the source to the destination.
    elif not in_place:
        files.copy(filename, destination)


def resize_image(im, width, height):
    return correct_image_and_call(_resize, im, width, height) or im


def make_cover(filename, destination=None):
    """
    Create a cover image file; if `destination` is passed, a new file will be
    created and the original left unaltered, else the original file will be
    altered.
    """
    resize(filename, *COVER_SIZE, destination=destination)


def correct_image_and_call(f, im, *a, **kw):
    """
    Call a function, passing in an image where the canvas size of each frame is
    the same.

    The function can return an image to post-process or None.
    """

    animated = len(im) > 1
    # either of these operations make the image satisfy the contraint
    # `all(im.size == frame.size for frame in im)`
    if animated:
        im = im.coalesced()
    else:
        im = im.cropped(im[0].canvas)
    # returns a new image to post-process or None
    im = f(im, *a, **kw)
    if animated and im is not None:
        im = im.optimized_for_animated_gif()
    return im


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
    ret = correct_image_and_call(_shrinkcrop, im, size, bounds)
    if ret.size != size or (len(ret) == 1 and ret[0].size != size):
        ignored_sizes = ret.size, ret[0].size  # to log these locals
        raise WeasylError('thumbnailingMessedUp')
        ignored_sizes  # to shut pyflakes up
    return ret

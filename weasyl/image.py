# favorite.py

import logging
import os

from sanpera.exception import SanperaError
from sanpera.image import Image
from sanpera import geometry
import web

from libweasyl import images

from weasyl import files
from weasyl.error import WeasylError


def read(filename):
    try:
        return Image.read(filename)
    except SanperaError:
        web.ctx.log_exc(level=logging.DEBUG)
        raise WeasylError('imageDecodeError')


def from_string(filedata):
    try:
        return Image.from_buffer(filedata)
    except SanperaError:
        web.ctx.log_exc(level=logging.DEBUG)
        raise WeasylError('imageDecodeError')


def image_setting(im):
    if im.original_format in ('JPG', 'JPEG'):
        return 'J'
    if im.original_format == 'PNG':
        return 'P'
    if im.original_format == 'GIF':
        return 'G'


def check_crop(image_size, crop_bounds):
    """
    Return True if the specified crop rectangle is valid, else False.
    """
    image_bounds = image_size.at(geometry.origin)
    return bool(crop_bounds) and crop_bounds in image_bounds


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
    if not images.image_extension(im):
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


def make_cover(filename, destination=None):
    """
    Create a cover image file; if `destination` is passed, a new file will be
    created and the original left unaltered, else the original file will be
    altered.
    """
    resize(filename, *images.COVER_SIZE, destination=destination)


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

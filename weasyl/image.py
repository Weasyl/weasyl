from sanpera.exception import SanperaError
from sanpera.image import Image
from sanpera import geometry

from libweasyl import images


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


def make_cover(filename, destination=None):
    """
    Create a cover image file; if `destination` is passed, a new file will be
    created and the original left unaltered, else the original file will be
    altered.
    """
    im = images.make_cover_image(images.read(filename))
    im.write(destination or filename)

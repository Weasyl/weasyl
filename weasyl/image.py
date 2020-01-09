from __future__ import absolute_import

import os

from PIL import Image
from libweasyl import images

from weasyl import files
from weasyl.error import WeasylError


def image_setting(im):
    if im.file_format == "jpg":
        return 'J'
    if im.file_format == 'png':
        return 'P'
    if im.file_format == 'gif':
        return 'G'


def check_type(filename):
    """
    Return True if the filename corresponds to an image file, else False.
    """
    try:
        im = Image.open(filename)
    except IOError:
        return False
    else:
        return im.format in ['JPEG', 'PNG', 'GIF']


def make_cover(filename, destination=None):
    """
    Create a cover image file; if `destination` is passed, a new file will be
    created and the original left unaltered, else the original file will be
    altered.
    """
    in_place = False
    if not destination:
        destination = filename + '.new'
        in_place = True

    im = images.WeasylImage(fp=filename)
    if not im.image_extension:
        raise WeasylError("FileType")

    files.ensure_file_directory(filename)
    im.resize(images.COVER_SIZE)
    if im is not None:
        im.save(destination)
        if in_place:
            os.rename(destination, filename)

    # if there's no need to resize, in-place resize is a no-op. otherwise copy
    # the source to the destination.
    elif not in_place:
        files.copy(filename, destination)

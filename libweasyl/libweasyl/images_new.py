# encoding: utf-8

"""
Image manipulation with Pillow.
"""
# TODO: rename when Sanpera libweasyl.libweasyl.images is no longer used

from __future__ import absolute_import

from collections import namedtuple
from io import BytesIO

from PIL import Image

from .images import THUMB_HEIGHT


_WEBP_ENABLED = False

ThumbnailFormats = namedtuple('ThumbnailFormats', ['compatible', 'webp'])


def get_thumbnail_spec(size, height):
    """
    Get the source rectangle (x, y, x + w, y + h) and result size (w, h) for
    the thumbnail of the specified height of an image with the specified size.
    """
    size_width, size_height = size

    max_source_width = 2 * max(size_height, height)
    max_source_height = max(2 * size_width, height)

    source_width = min(size_width, max_source_width)
    source_height = min(size_height, max_source_height)
    source_left = (size_width - source_width) // 2
    source_top = 0

    result_height = min(size_height, height)
    result_width = (source_width * result_height + source_height // 2) // source_height

    return (
        (source_left, source_top, source_left + source_width, source_top + source_height),
        (result_width, result_height),
    )


def get_thumbnail_spec_cropped(rect, height):
    """
    Get the source rectangle and result size for the thumbnail of the specified
    height of a specified rectangular section of an image.
    """
    left, top, right, bottom = rect
    inner_rect, result_size = get_thumbnail_spec((right - left, bottom - top), height)
    inner_left, inner_top, inner_right, inner_bottom = inner_rect

    return (inner_left + left, inner_top + top, inner_right + left, inner_bottom + top), result_size


def _fit_inside(rect, size):
    left, top, right, bottom = rect
    width, height = size

    return (
        max(0, left),
        max(0, top),
        min(width, right),
        min(height, bottom),
    )


def get_thumbnail(image_file, bounds=None):
    """
    Get an iterable of (bytes, file_type, attributes) tuples, each a
    representation of an image’s thumbnail in some format. The image can be a
    path or a file object.
    """
    image = Image.open(image_file)
    image_format = image.format

    if bounds is None:
        source_rect, result_size = get_thumbnail_spec(image.size, THUMB_HEIGHT)
    else:
        source_rect, result_size = get_thumbnail_spec_cropped(
            _fit_inside(bounds, image.size),
            THUMB_HEIGHT)

    if source_rect == (0, 0, image.width, image.height):
        image.draft(None, result_size)
        image = image.resize(result_size, resample=Image.LANCZOS)
    else:
        # TODO: draft and adjust rectangle?
        image = image.resize(result_size, resample=Image.LANCZOS, box=source_rect)

    thumbnail_attributes = {'width': image.width, 'height': image.height}

    if image_format == 'JPEG':
        with BytesIO() as f:
            image.save(f, format='JPEG', quality=95, optimize=True, progressive=True, subsampling='4:2:2')
            compatible = (f.getvalue(), 'jpg', thumbnail_attributes)

        lossless = False
    elif image_format == 'PNG':
        with BytesIO() as f:
            image.save(f, format='PNG', optimize=True)
            compatible = (f.getvalue(), 'png', thumbnail_attributes)

        lossless = True
    elif image_format == 'GIF':
        with BytesIO() as f:
            image.save(f, format='GIF', optimize=True)
            compatible = (f.getvalue(), 'gif', thumbnail_attributes)

        lossless = True
    else:
        raise Exception("Unexpected image format: %r" % (image_format,))

    if _WEBP_ENABLED:
        with BytesIO() as f:
            image.save(f, format='WebP', lossless=lossless, quality=100 if lossless else 90)
            webp = (f.getvalue(), 'webp', thumbnail_attributes)
    else:
        webp = None

    return ThumbnailFormats(compatible, webp)

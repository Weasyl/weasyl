# encoding: utf-8

"""
Image manipulation with Pillow.
"""
# TODO: rename when Sanpera libweasyl.libweasyl.images is no longer used

from collections import namedtuple
from io import BytesIO

from PIL import Image

from .images import THUMB_HEIGHT


ThumbnailFormats = namedtuple('ThumbnailFormats', ['compatible', 'webp'])

_BACKGROUND_COLOR = (0x1f, 0x2b, 0x33, 0xff)


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


def _has_transparency(image):
    assert image.mode in ('RGB', 'RGBA')
    return image.mode == 'RGBA' and image.getextrema()[3][0] != 255


def get_thumbnail(image_file, bounds=None):
    """
    Get an iterable of (bytes, file_type, attributes) tuples, each a
    representation of an image’s thumbnail in some format. The image can be a
    path or a file object.
    """
    image = Image.open(image_file)

    # this is checked before getting to the point of creating a thumbnail
    assert image.format in ('JPEG', 'MPO', 'PNG', 'GIF')

    # JPEG/MPO: L, RGB, CMYK
    # PNG: 1, L, LA, I, P, RGB, RGBA
    # GIF: L, P
    if image.mode in ('1', 'L', 'LA', 'I', 'P', 'CMYK'):
        with image:
            image = image.convert(mode='RGBA' if image.mode == 'LA' or 'transparency' in image.info else 'RGB')

    if bounds is None:
        source_rect, result_size = get_thumbnail_spec(image.size, THUMB_HEIGHT)
    else:
        source_rect, result_size = get_thumbnail_spec_cropped(
            _fit_inside(bounds, image.size),
            THUMB_HEIGHT)

    if source_rect == (0, 0, image.width, image.height):
        image.draft(None, result_size)
        with image:
            image = image.resize(result_size, resample=Image.Resampling.LANCZOS)
    else:
        # TODO: draft and adjust rectangle?
        with image:
            image = image.resize(result_size, resample=Image.Resampling.LANCZOS, box=source_rect)

    thumbnail_attributes = {'width': image.width, 'height': image.height}

    with BytesIO() as f:
        image.save(f, format='WebP', quality=90, method=6)
        webp = (f.getvalue(), 'webp', thumbnail_attributes)

    if _has_transparency(image):
        # IE11, only relevant browser not to support WebP, gets no transparency in thumbnails
        background = Image.new('RGBA', image.size, color=_BACKGROUND_COLOR)
        with image:
            image = Image.alpha_composite(background, image)

    if image.mode == 'RGBA':
        with image:
            image = image.convert('RGB')

    with image, BytesIO() as f:
        image.save(f, format='JPEG', quality=90, optimize=True, progressive=True, subsampling='4:2:2')
        compatible = (f.getvalue(), 'jpg', thumbnail_attributes)

    return ThumbnailFormats(compatible, webp)

"""
Image manipulation.

This module defines functions which work on sanpera_ ``Image`` objects.

.. _sanpera: https://pypi.python.org/pypi/sanpera
"""

from __future__ import division

from sanpera.image import Image
from sanpera import geometry

from libweasyl.exceptions import ThumbnailingError


COVER_SIZE = 1024, 3000
"The maximum size of a cover image, in pixels."

THUMB_HEIGHT = 250
"The maximum height of a thumbnail, in pixels."


read = Image.read
"""
libweasyl.images.read(*filename*)

Read an ``Image`` from disk using the given filename.

Parameters:
    filename: The filename of the image to load.

Returns:
    A sanpera ``Image``.
"""

from_buffer = Image.from_buffer
"""
libweasyl.images.from_buffer(*data*)

Parse some data into an ``Image``.

Parameters:
    data: :term:`bytes`.

Returns:
    A sanpera ``Image``.
"""


IMAGE_EXTENSIONS = {
    b'JPG': '.jpg',
    b'JPEG': '.jpg',
    b'PNG': '.png',
    b'GIF': '.gif',
}


def image_extension(im):
    """
    Given a sanpera ``Image``, return the file extension corresponding with the
    original format of the image.

    Parameters:
        im: A sanpera ``Image``.

    Returns:
        :term:`native string`: one of ``.jpg``, ``.png``, ``.gif``, or ``None``
        if the format was unknown.
    """
    return IMAGE_EXTENSIONS.get(im.original_format)


def image_file_type(im):
    """
    Given a sanpera ``Image``, return the file type of the original format of
    the image.

    This is basically the same as :py:func:`.image_extension`, except it
    doesn't return a leading ``.`` on the format.

    Parameters:
        im: A sanpera ``Image``.

    Returns:
        :term:`native string`: one of ``jpg``, ``png``, ``gif``, or ``None`` if
        the format was unknown.
    """
    ret = image_extension(im)
    if ret is not None:
        ret = ret.lstrip('.')
    return ret


def unanimate(im):
    """
    Get the non-animated version of a sanpera ``Image``.

    Paramters:
        im: A sanpera ``Image``.

    Returns:
        *im*, if it wasn't animated, or a new ``Image`` with just the first
        frame of *im* if it was.
    """
    if len(im) == 1:
        return im
    ret = Image()
    ret.append(im[0])
    return ret


def correct_image_and_call(f, im, *a, **kw):
    """
    Call a function, passing in an image where the canvas size of each frame is
    the same.

    The function will be called as ``f(im, *a, **kw)`` and can return an image
    to post-process or ``None``. Post-processing is currently limited to
    optimizing animated GIFs.

    Parameters:
        f: The function to call.
        im: A sanpera ``Image``.
        *a: Positional arguments with which to call *f*.
        **kw: Keyword arguments with which to call *f*.

    Returns:
        *im*, if *f* returned ``None``, or the ``Image`` returned by *f* after
        post-processing.
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


def _resize(im, width, height):
    # resize only if we need to; return None if we don't
    if im.size.width > width or im.size.height > height:
        im = im.resized(im.size.fit_inside((width, height)))
        return im


def resize_image(im, width, height):
    """
    Resize an image if necessary. Will not resize images that fit entirely
    within target dimensions.

    Parameters:
        im: A sanpera ``Image``.
        width: The maximum width, in pixels.
        height: The maximum height, in pixels.

    Returns:
        *im*, if the image is smaller than the given *width* and *height*.
        Otherwise, a new ``Image`` resized to fit.
    """
    return correct_image_and_call(_resize, im, width, height) or im


def make_cover_image(im):
    """
    Make a cover image.

    That is, resize an image to be smaller than :py:data:`COVER_SIZE` if
    necessary.

    Parameters:
        im: A sanpera ``Image``.

    Returns:
        *im*, if the image is smaller than :py:data:`COVER_SIZE`. Otherwise, a
        new ``Image`` resized to fit.
    """
    return resize_image(im, *COVER_SIZE)


def _height_resize(im, height, bounds=None):
    """Creates an image scaled to no more than the specified height with 0.5 <= aspect ratio <= 2."""
    def crop_image_to_width(image, width):  # Crops from both sides equally.
        overflow = image.size.width - width
        border = overflow / 2
        crop_rect = geometry.Rectangle(border, 0, border + width, image.size.height)
        return image.cropped(crop_rect)

    def crop_image_to_height(image, height):  # Crops from the bottom.
        crop_rect = geometry.Rectangle(0, 0, image.size.width, height)
        return image.cropped(crop_rect)

    def scale_image_to_height(image, height):
        new_width = (image.size.width * height) / image.size.height
        return image.resized((new_width, height))

    if bounds is not None:
        # TODO: Add some checks here. e.g. make sure bounds are smaller
        # than the original image.
        if bounds.size != im.size:
            im = im.cropped(bounds)

    aspect_ratio = float(im.size.width) / im.size.height

    if im.size.height > height:
        if aspect_ratio > 2:  # Image is too wide.
            thumb = crop_image_to_width(im, im.size.height * 2)
        elif aspect_ratio < 0.5:  # Image is too tall.
            new_height = im.size.width * 2
            if new_height < height:
                new_height = height
            thumb = crop_image_to_height(im, new_height)
        else:
            thumb = im
        thumb = scale_image_to_height(thumb, height)
    else:  # Height `height` or less.
        if im.size.width > height * 2:
            thumb = crop_image_to_width(im, height * 2)
        else:
            thumb = im
    return thumb


def height_resize(im, height, bounds=None):
    """
    Resize and crop an image to look good at a specified height.

    The image is resized and cropped according to the following rules:
    If *im* is not taller than *height*, its width is checked. If it is wider than
    2 * *height*, it will be cropped from both sides down to 2 * *height* width.
    If the *im* is taller than *height* its aspect ratio is considered: If *im* is
    more than twice as wide as it is tall, it will be cropped equally from both
    left and right to be twice as wide as it is tall. If *im* is more than twice as
    tall as it is wide, it will be cropped from the bottom to be twice as tall as it
    is wide, but not if this would make it shorter than *height*.
    After cropping is considered, the image will be resized proportionally to be
    *height* pixels tall.


    Parameters:
        im: A sanpera ``Image``.
        size: The desired height of the resulting image.
        bounds: Optionally, a sanpera ``Rectangle`` to use to crop *im* before
            resizing it.

    Returns:
        *im*, if it is no taller than *height* and no wider than 2 * *height*.
        Otherwise, a new ``Image`` resized and/or cropped according to the rules
        above.
    """
    ret = correct_image_and_call(_height_resize, im, height, bounds)
    if ret.size.height > height or (len(ret) == 1 and ret[0].size.height > height):
        # This is a sanity test to make sure the output of _height_resize()
        # conforms to our height contract.
        raise ThumbnailingError(ret.size, ret[0].size)
    return ret


def make_thumbnail(im, bounds=None):
    """
    Make a thumbnail.

    That is, resize an image to be no taller than :py:data:`THUMB_HEIGHT` if
    necessary after unanimating it and maintain a reasonable aspect ratio (2x)
    if possible.

    Parameters:
        im: A sanpera ``Image``.
        bounds: Optionally, a sanpera ``Rectangle`` to use to crop *im* before
            generating a thumbnail from it.

    Returns:
        *im*, if the image is smaller than :py:data:`THUMB_HEIGHT` by twice
        :py:data:`THUMB_HEIGHT` and contains only a single frame. Otherwise,
        a new single-frame ``Image`` resized to fit within the bounds.
    """
    return height_resize(unanimate(im), THUMB_HEIGHT, bounds)

"""
File manipulation and detection.
"""
import errno
import os


from libweasyl.constants import Category
from libweasyl.exceptions import InvalidFileFormat, UnknownFileFormat
from libweasyl import images


def makedirs_exist_ok(path):
    """
    Ensure a directory and all of its parent directories exist.

    This is different from :py:func:`os.makedirs` in that it will not raise an
    exception if the directory already exists. Any other exceptions (e.g.
    permissions failure; filesystem out of inodes) will still propagate.

    This is functionally equivalent to specifying ``os.makedirs(path,
    exist_ok=True)`` in python 3.2+, but exists in libweasyl for compatibility
    with python 2.7.

    Parameters:
        path: The directory whose existence must be ensured.
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def fanout(name, fanout):
    """
    Generate fanout for a particular name.

    For example:

    .. code-block:: pycon

      >>> fanout('spam', [1, 2])
      ['s', 'pa']
      >>> fanout('spameggs', [2, 2, 2])
      ['sp', 'am', 'eg']

    Parameters:
        name: The name to fan out. Can be any sliceable sequence; usually a
            string.
        fanout: A sequence indicating how many characters per segment should be
            included.

    Returns:
        A list of the segments sliced from *name*.
    """
    ret = []
    pos = 0
    for length in fanout:
        ret.append(name[pos:pos + length])
        pos += length
    return ret


def file_type_for_category(data, category):
    """
    Determine the type of a file, given its contents and a submission category.

    This function attempts to guess the type of a file using very basic
    heuristics. Returning a particular type *does not* mean that the file is
    valid data in the type specified, but merely that it resembles a file of
    that type.

    - Visual submissions are first decoded and then checked to ensure that
      their format is GIF, JPG, or PNG.
    - Literary submissions check for and explicitly disallow RTF documents and
      some Microsoft Word formats. If the document is not a PDF, it must be
      valid UTF-8 text.
    - Multimedia submissions must resemble a SWF or an MP3.

    Parameters:
        data: The ``bytes`` of the file.
        category: A :py:class:`.Category`.

    Returns:
        A tuple of ``decoded, format``. ``decoded`` is either ``None`` (to
        indicate that no decoding can easily be done) or the decoded submission
        data in some format. Visual submissions will return the decoded sanpera
        ``Image`` object; non-PDF literary submissions will return the decoded
        UTF-8 text. ``format`` will be a :term:`native string`: one of ``gif``,
        ``jpg``, ``png``, ``pdf``, ``txt``, ``swf``, or ``mp3``.
    """
    if category == Category.visual:
        try:
            im = images.WeasylImage(string=data)
        except IOError:
            raise UnknownFileFormat('The image data provided could not be decoded.')
        fmt = im.file_format if im.file_format else None
        if fmt not in {'gif', 'png', 'jpg'}:
            raise InvalidFileFormat('Image files must be in the GIF, JPG, or PNG formats.')
        return im, fmt
    elif category == Category.literary:
        if data.startswith(b'%PDF'):
            return None, 'pdf'
        elif data.startswith(b'{\\rtf1'):
            raise InvalidFileFormat('RTF documents are not allowed.')
        elif data.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            raise InvalidFileFormat('Microsoft Word documents are not allowed.')
        else:
            try:
                return data.decode('utf-8'), 'txt'
            except UnicodeDecodeError:
                raise UnknownFileFormat('UTF-8 encoding is required for Markdown documents.')
    elif category == Category.multimedia:
        if data.startswith((b'CWS', b'FWS', b'ZWS')):
            return None, 'swf'
        elif data.startswith((b'ID3', b'\xff\xfb')):
            return None, 'mp3'
        else:
            raise UnknownFileFormat('Multimedia documents must be in the SWF or MP3 formats.')
    else:
        raise ValueError('unknown submission category', category)

from __future__ import unicode_literals

import errno

import pytest

from libweasyl.constants import Category
from libweasyl.test.common import datadir
from libweasyl import exceptions, files


def test_makedirs_default_behavior(tmpdir):
    """
    ``makedirs_exist_ok`` creates multiple levels of directories.
    """
    d = tmpdir.join('a', 'b', 'c')
    assert not d.exists()
    files.makedirs_exist_ok(d.strpath)
    assert d.exists()


def test_makedirs_with_extant_directories(tmpdir):
    """
    ``makedirs_exist_ok`` doesn't care if the directories already exist.
    """
    d = tmpdir.join('a', 'b', 'c')
    d.ensure(dir=True)
    files.makedirs_exist_ok(d.strpath)
    assert d.exists()


def test_makedirs_reraises_other_errors(tmpdir):
    """
    ``makedirs_exist_ok`` reraises errors it can't handle, such as EACCES.
    """
    tmpdir.chmod(0)
    d = tmpdir.join('a', 'b', 'c')
    with pytest.raises(OSError) as e:
        files.makedirs_exist_ok(d.strpath)
    assert e.value.errno == errno.EACCES


def test_file_type_for_category_invalid_category():
    """
    ``file_type_for_category`` raises an exception on unknown categories.
    """
    with pytest.raises(ValueError):
        files.file_type_for_category(b'', 'spam')


def test_file_type_for_category_invalid_visual_file():
    """
    ``UnknownFileFormat`` is raised if invalid image data is passed in for a
    visual submission.
    """
    with pytest.raises(exceptions.UnknownFileFormat):
        files.file_type_for_category(b'', Category.visual)


def test_file_type_for_category_invalid_file_format():
    """
    ``InvalidFileFormat`` is raised if the image data isn't a GIF, JPG, or PNG.
    """
    data = datadir.join('1x70.bmp').read(mode='rb')
    with pytest.raises(exceptions.InvalidFileFormat):
        files.file_type_for_category(data, Category.visual)


@pytest.mark.parametrize(('filename', 'expected_size', 'expected_fmt'), [
    ('1x70.gif', (1, 70), 'gif'),
    ('1x70.jpg', (1, 70), 'jpg'),
    ('2x233.gif', (2, 233), 'gif'),
    ('1200x6566.png', (1200, 6566), 'png'),
])
def test_file_type_for_category_visual_results(filename, expected_size, expected_fmt):
    """
    ``file_type_for_category`` will, for visual submissions, return the decoded
    image and its file format.
    """
    data = datadir.join(filename).read(mode='rb')
    decoded, fmt = files.file_type_for_category(data, Category.visual)
    assert fmt == expected_fmt
    assert tuple(decoded.size) == expected_size


def test_file_type_for_category_detects_pdfs():
    """
    PDF files are detected but not decoded.
    """
    assert files.file_type_for_category(b'%PDF spam eggs', Category.literary) == (None, 'pdf')


def test_file_type_for_category_rejects_rtfs():
    """
    RTF files are explicitly rejected.
    """
    with pytest.raises(exceptions.InvalidFileFormat):
        files.file_type_for_category(b'{\\rtf1}', Category.literary)


def test_file_type_for_category_rejects_word_documents():
    """
    Microsoft Word documents (at least, in one format) are also rejected.
    """
    with pytest.raises(exceptions.InvalidFileFormat):
        files.file_type_for_category(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', Category.literary)


def test_file_type_for_category_requires_utf8():
    """
    Non-PDF documents must be encoded in UTF-8, or an ``UnknownFileFormat``
    exception is raised.
    """
    with pytest.raises(exceptions.UnknownFileFormat):
        files.file_type_for_category(b'\xff', Category.literary)


def test_file_type_for_category_literary_results():
    """
    Non-PDF UTF-8 documents are returned decoded.
    """
    assert files.file_type_for_category(b'hello\xc3\xbfworld', Category.literary) == (u'hello\xffworld', 'txt')

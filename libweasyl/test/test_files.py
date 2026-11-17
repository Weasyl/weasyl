import pytest

from libweasyl.constants import Category
from libweasyl import exceptions, files


def test_file_type_for_category_invalid_category():
    """
    ``file_type_for_category`` raises an exception on unknown categories.
    """
    with pytest.raises(ValueError):
        files.file_type_for_category(b'', 'spam')


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
    assert files.file_type_for_category(b'hello\xc3\xbfworld', Category.literary) == ('hello\xffworld', 'txt')

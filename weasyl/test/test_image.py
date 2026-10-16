import pytest

from weasyl import image


def test_unsupported_format():
    with pytest.raises(image.UnsupportedFormat):
        image.create_cover(rb'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"></svg>')


def test_unrecognized_format():
    with pytest.raises(image.UnsupportedFormat):
        image.create_cover(b"woop")

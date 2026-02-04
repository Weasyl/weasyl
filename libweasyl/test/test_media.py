import pytest

from libweasyl.test.common import datadir
from libweasyl import images, media


def test_fetch_or_create_disk_media_item(staticdir, db):
    """
    ``MediaItem.fetch_or_create`` by default creates a disk media item,
    populates its attributes, and stores the file on disk.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    item = media.MediaItem.fetch_or_create(data, file_type='png')
    assert item.sha256 == 'a5deef985bde4438969b5f74a1864f7a5b1d127df3197b4fadf3f855201278b4'
    assert item.file_type == 'png'
    assert staticdir.joinpath(
        'static', 'media', 'a5', 'de', 'ef', 'a5deef985bde4438969b5f74a1864f7a5b1d127df3197b4fadf3f855201278b4.png'
    ).read_bytes() == data


def test_fetch_or_create_disk_media_item_with_attributes(db):
    """
    Attributes can be passed in, which propagate to the media item object.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    item = media.MediaItem.fetch_or_create(data, file_type='png', attributes={'spam': 'eggs'})
    assert item.attributes == {'spam': 'eggs'}


def test_fetch_or_create_disk_media_item_with_image(db):
    """
    An image can be passed in, which pulls out width/height attributes and
    autodetects the file type.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    im = images.from_buffer(data)
    item = media.MediaItem.fetch_or_create(data, im=im)
    assert item.file_type == 'png'
    assert item.attributes == {'width': 1200, 'height': 6566}


def test_fetch_or_create_disk_media_item_with_image_and_attributes(db):
    """
    Passing an image and attributes merges the two sets of attributes.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    im = images.from_buffer(data)
    item = media.MediaItem.fetch_or_create(data, file_type='png', im=im, attributes={'spam': 'eggs'})
    assert item.attributes == {'spam': 'eggs', 'width': 1200, 'height': 6566}


def test_fetch_or_create_disk_media_item_fetches_extant_items(db):
    """
    Calling ``MediaItem.fetch_or_create`` with data that's already in the
    database gives back the extant media item.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    item1 = media.MediaItem.fetch_or_create(data, file_type='png')
    db.flush()
    item2 = media.MediaItem.fetch_or_create(data, file_type='png')
    assert item1.mediaid == item2.mediaid


def test_fetch_or_create_requires_file_type():
    """
    A file type is required if an image isn't being passed in.
    """
    with pytest.raises(ValueError) as err:
        media.MediaItem.fetch_or_create(b'spam')
    assert str(err.value) == "a file type is required"


def test_disk_media_item_display_url(db):
    """
    Disk media items have a display_url that's fanned out from /static/media.
    """
    data = datadir.join('1200x6566.png').read(mode='rb')
    item = media.MediaItem.fetch_or_create(data, file_type='png')
    assert item.display_url == (
        '/static/media/a5/de/ef/a5deef985bde4438969b5f74a1864f7a5b1d127df3197b4fadf3f855201278b4.png')


def test_disk_media_item_display_url_ax_rule(db):
    """
    The display_url replaces ``media/ad`` with ``media/ax`` because adblock
    sucks.
    """
    data = datadir.join('1x70.gif').read(mode='rb')
    item = media.MediaItem.fetch_or_create(data, file_type='gif')
    assert item.display_url == (
        '/static/media/ax/b2/06/adb20677ffcfda9605812f7f47aaa94a9c9b3e1a0b365e43872dc55199f5f224.gif')

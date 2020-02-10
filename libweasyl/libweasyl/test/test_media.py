from __future__ import unicode_literals

import contextlib

import pytest
from pyramid.decorator import reify

from libweasyl.test.common import Bag, datadir
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
    assert staticdir.join(
        'static', 'media', 'a5', 'de', 'ef', 'a5deef985bde4438969b5f74a1864f7a5b1d127df3197b4fadf3f855201278b4.png'
    ).read(mode='rb') == data


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
    pytest.raises(ValueError, media.MediaItem.fetch_or_create, b'spam')


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


class MediaBag(Bag):
    @reify
    def media(self):
        raise AssertionError('tried to access the media attribute of a MediaBag')


def test_media_attribute_blows_up():
    """
    MediaBags can't have their media attribute fetched without an exception
    being raised.
    """
    with pytest.raises(AssertionError):
        MediaBag().media


def test_media_attribute_is_fine_after_being_set():
    """
    MediaBags don't care about the media attribute being accessed if it's
    filled in by something else.
    """
    b = MediaBag()
    b.media = None
    assert b.media is None


@contextlib.contextmanager
def build_multi_get(expected_length):
    called = []

    def multi_get(*keys):
        assert len(keys) == expected_length
        called.append(True)
        return keys

    yield multi_get
    assert called


def test_populator():
    """
    Populators fill the media attribute on objects passed in.
    """
    o1, o2 = MediaBag(id=1), MediaBag(id=2)
    with build_multi_get(2) as multi_get:
        media.build_populator('id', multi_get)([o1, o2])
    assert (o1.media, o2.media) == (1, 2)


def test_populator_alternate_attribute():
    """
    Populators don't care what the identity attribute is called.
    """
    o1, o2 = MediaBag(iid=1), MediaBag(iid=2)
    with build_multi_get(2) as multi_get:
        media.build_populator('iid', multi_get)([o1, o2])
    assert (o1.media, o2.media) == (1, 2)


def test_populator_dedup():
    """
    Populators only call their multi-get function with a unique set of objects.
    That is, the multi-get function won't get called with two identical
    objects.
    """
    o1, o2 = MediaBag(id=1), MediaBag(id=2)
    objs = [o1, o2, o1, o2]
    with build_multi_get(2) as multi_get:
        media.build_populator('id', multi_get)(objs)
    assert objs == [o1, o2, o1, o2]


def test_populator_only_fetches_needy():
    """
    Only objects without a media attribute will be passed to the multi-get
    function. Additionally, the media attribute won't be queried directly for
    its existence.
    """
    o1, o2 = MediaBag(id=1), MediaBag(media=2)
    with build_multi_get(1) as multi_get:
        media.build_populator('id', multi_get)([o1, o2])


def test_populator_aborts_early():
    """
    If there's no media to fetch, the multi-get function won't get called.
    """
    o1, o2 = MediaBag(media=1), MediaBag(media=2)

    def multi_get(*keys):
        raise AssertionError('tried calling multi_get')

    objs = [o1, o2]
    media.build_populator('id', multi_get)(objs)
    assert objs == [o1, o2]

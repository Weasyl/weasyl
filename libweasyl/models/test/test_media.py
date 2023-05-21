import pytest

from libweasyl.models import media
from libweasyl.test.common import media_item, make_user, make_submission


link_types_names = 'cls', 'linked_attr', 'link_attr', 'media_attr', 'generator'
link_types = [
    (media.UserMediaLink, 'userid', 'userid', 'mediaid', make_user),
    (media.SubmissionMediaLink, 'submitid', 'submitid', 'mediaid', make_submission),
]


@pytest.mark.parametrize(link_types_names, link_types)
def test_creating_media_links(db, cls, linked_attr, link_attr, media_attr, generator):
    """
    Media links can be created from different types of objects to media items.
    """
    linked = generator(db)
    item = media_item(db, '1200x6566.png')
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test', item)
    [link] = cls.query.all()
    assert link.link_type == 'test'
    assert getattr(link, link_attr) == getattr(linked, linked_attr)
    assert getattr(link, media_attr) == item.mediaid


@pytest.mark.parametrize(link_types_names, link_types)
def test_replacing_media_links(db, cls, linked_attr, link_attr, media_attr, generator):
    """
    Media links with the same name get replaced by default.
    """
    linked = generator(db)
    item1 = media_item(db, '1200x6566.png')
    item2 = media_item(db, '1x70.gif')
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test', item1)
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test', item2)
    [link] = cls.query.all()
    assert link.link_type == 'test'
    assert getattr(link, link_attr) == getattr(linked, linked_attr)
    assert getattr(link, media_attr) == item2.mediaid


@pytest.mark.parametrize(link_types_names, link_types)
def test_multiple_media_links(db, cls, linked_attr, link_attr, media_attr, generator):
    """
    Multiple media links from a single object are possible as long as each link
    has a different name.
    """
    linked = generator(db)
    item1 = media_item(db, '1200x6566.png')
    item2 = media_item(db, '1x70.gif')
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test1', item1)
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test2', item2)
    [link1, link2] = cls.query.order_by(getattr(cls, media_attr).asc()).all()
    assert link1.link_type == 'test1'
    assert getattr(link1, link_attr) == getattr(linked, linked_attr)
    assert getattr(link1, media_attr) == item1.mediaid
    assert link2.link_type == 'test2'
    assert getattr(link2, link_attr) == getattr(linked, linked_attr)
    assert getattr(link2, media_attr) == item2.mediaid


@pytest.mark.parametrize(link_types_names, link_types)
def test_clearing_media_links(db, cls, linked_attr, link_attr, media_attr, generator):
    """
    A media link can also be cleared.
    """
    linked = generator(db)
    item = media_item(db, '1200x6566.png')
    cls.make_or_replace_link(getattr(linked, linked_attr), 'test', item)
    cls.clear_link(getattr(linked, linked_attr), 'test')
    assert cls.query.count() == 0

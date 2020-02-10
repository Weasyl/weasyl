from __future__ import absolute_import

import contextlib

import pytest

from weasyl import media


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
    Populators fill the media key on objects passed in.
    """
    o1, o2 = dict(id=1), dict(id=2)
    with build_multi_get(2) as multi_get:
        media.build_populator('id', 'media', multi_get)([o1, o2])
    assert (o1['media'], o2['media']) == (1, 2)


def test_populator_alternate_key():
    """
    Populators don't care what the identity key is called.
    """
    o1, o2 = dict(iid=1), dict(iid=2)
    with build_multi_get(2) as multi_get:
        media.build_populator('iid', 'media', multi_get)([o1, o2])
    assert (o1['media'], o2['media']) == (1, 2)


@pytest.mark.xfail(strict=True, reason="weasyl.media doesn't deduplicate like libweasyl.media did (yet)")
def test_populator_dedup():
    """
    Populators only call their multi-get function with a unique set of objects.
    That is, the multi-get function won't get called with two identical
    objects.
    """
    o1, o2 = dict(id=1), dict(id=2)
    objs = [o1, o2, o1, o2]
    with build_multi_get(2) as multi_get:
        media.build_populator('id', 'media', multi_get)(objs)
    assert objs == [o1, o2, o1, o2]


@pytest.mark.xfail(strict=True, reason="weasyl.media doesn't check for existing media like libweasyl.media did (yet)")
def test_populator_only_fetches_needy():
    """
    Only objects without a media key will be passed to the multi-get function.
    Additionally, the media key won't be queried directly for its existence.
    """
    o1, o2 = dict(id=1), dict(id=2, media=2)
    with build_multi_get(1) as multi_get:
        media.build_populator('id', 'media', multi_get)([o1, o2])


@pytest.mark.parametrize('objs_in', [
    [],
    pytest.param(
        [dict(id=1, media=1), dict(id=2, media=2)],
        marks=pytest.mark.xfail(strict=True, reason="weasyl.media doesn't check for existing media like libweasyl.media did (yet)")),
])
def test_populator_aborts_early(objs_in):
    """
    If there's no media to fetch, the multi-get function won't get called.
    """
    def multi_get(*keys):
        raise AssertionError('tried calling multi_get')

    objs = objs_in[:]
    media.build_populator('id', 'media', multi_get)(objs)
    assert objs == objs_in

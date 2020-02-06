"""
Cache configuration.

This works in conjunction with dogpile.cache_ to provide caching for any Weasyl
project.

.. _dogpile.cache: http://dogpilecache.readthedocs.org/en/latest/
"""

import os
import re
import threading
import zlib

import json
from dogpile.cache.api import CachedValue, NO_VALUE
from dogpile.cache.proxy import ProxyBackend
from dogpile.cache import make_region


_GZIP_THRESHOLD = 1024 * 1024
_MEMCACHED_PREFIX = os.environ.get('WEASYL_MEMCACHED_PREFIX', '') + ':'
_bad_key_regexp = re.compile('[\x00-\x20\x7f]')


def escape_key(key):
    """
    Escape a key so that it is valid for use in memcached.

    Basically, this just removes nonprintable characters and replaces them with
    a period (i.e. ``.``).

    Parameters:
        key: A :term:`native string`.

    Returns:
        An escaped :term:`native string`.
    """
    key = str(key)
    return _bad_key_regexp.sub('.', key)


def key_mangler(key):
    """
    Transform keys before they are sent to memcached.

    This escapes *key* with :py:func:`escape_key` and then prepends a prefix
    derived from the :envvar:`WEASYL_MEMCACHED_PREFIX` environment variable.

    Parameters:
        key: A :term:`native string`.

    Returns:
        An escaped, prefixed :term:`native string`.
    """
    return _MEMCACHED_PREFIX + escape_key(key)


region = make_region(key_mangler=key_mangler)


class ThreadCacheProxy(ProxyBackend):
    """
    A thread-local caching proxy.

    What this means is that all of the requests made to memcached (or whatever)
    will be cached locally, and future requests will refer to the local cache
    instead of having to make another memcached round trip.

    This is convenient, but the cache must be periodically expired in order for
    changes in memcached to propagate to the application. :py:meth:`.zap_cache`
    will clear the entire cache for the current thread. It's intended to be
    called, for example, at the end of an HTTP request's lifetime.
    """

    _local = threading.local()

    @classmethod
    def zap_cache(cls):
        """
        Clear the cache for the current thread.

        If there wasn't any cache for the current thread, do nothing.
        """
        try:
            del cls._local.cache_dict
        except AttributeError:
            pass

    @property
    def _dict(self):
        """
        Get the cache dict for the current thread.

        Returns:
            dict: The cache dict.
        """
        if not hasattr(self._local, 'cache_dict'):
            self._local.cache_dict = {}
        return self._local.cache_dict

    def get(self, key):
        """
        Proxy a ``get`` call.

        If *key* is in the thread-local cache, return that. Otherwise, fetch
        from the proxied backend and store its result in the thread-local
        cache as long as the value was not
        :py:data:`~dogpile.cache.api.NO_VALUE`. Finally, return the fetched
        value.

        Parameters:
            key: A :term:`native string`.

        Returns:
            Some value, or :py:data:`~dogpile.cache.api.NO_VALUE` if the
            proxied backend returned that instead of a value.
        """
        d = self._dict
        if key in d:
            return d[key]
        ret = self.proxied.get(key)
        if ret is not NO_VALUE:
            d[key] = ret
        return ret

    def get_multi(self, keys):
        """
        Proxy a ``get_multi`` call.

        This works like :py:meth:`.get`, except *keys* is a list of keys, and
        the result is a list of values.

        Parameters:
            keys: A list of :term:`native string` objects.

        Returns:
            list: The values corresponding to the *keys*.
        """
        d = self._dict
        to_fetch = []
        ret = []
        for key in keys:
            ret.append(d.get(key, NO_VALUE))
            if ret[-1] is NO_VALUE:
                to_fetch.append((key, len(ret) - 1))
        if not to_fetch:
            return ret
        keys_to_fetch, indices = zip(*to_fetch)
        for key, index, value in zip(keys_to_fetch, indices, self.proxied.get_multi(keys_to_fetch)):
            if value is NO_VALUE:
                continue
            d[key] = ret[index] = value
        return ret

    def set(self, key, value):
        """
        Proxy a ``set`` call.

        The set is passed through to the proxied backend, and the *value* is
        stored in the thread-local cache under *key*.

        Parameters:
            key: A :term:`native string`.
            value: Some object.
        """
        self._dict[key] = value
        self.proxied.set(key, value)

    def set_multi(self, pairs):
        """
        Proxy a ``set_multi`` call.

        This works like :py:meth:`.set`, except *pairs* is a dict of key/value
        mappings instead of a single key/value mapping.

        Parameters:
            pairs (dict): A mapping :term:`native string` of objects to any
                objects.
        """
        self._dict.update(pairs)
        self.proxied.set_multi(pairs)

    def delete(self, key):
        """
        Proxy a ``delete`` call.

        The delete is passed through to the proxied backend, and the *key* is
        removed from the thread-local cache if it exists.

        Parameters:
            key: A :term:`native string`.
        """
        self._dict.pop(key, None)
        self.proxied.delete(key)

    def delete_multi(self, keys):
        """
        Proxy a ``delete_multi`` call.

        This works like :py:meth:`.delete`, except *keys* is a list of keys.

        Parameters:
            keys (list): A list of :term:`native string` objects.
        """
        d = self._dict
        for key in keys:
            d.pop(key, None)
        self.proxied.delete_multi(keys)


class JSONProxy(ProxyBackend):
    """
    A JSON-serializing proxy.

    Values passed through this proxy are serialized to or from JSON as they
    pass through, so that the proxied backend only has to worry about strings
    instead of python objects.

    Additionally, serialized JSON that is larger than a megabyte is
    transparently compressed.
    """

    def load(self, value):
        """
        Unserialize some data from JSON.

        If the JSON was compressed, decompress it first.

        Parameters:
            value: :py:data:`~dogpile.cache.api.NO_VALUE` or :term:`bytes`.

        Returns:
            :py:data:`~dogpile.cache.api.NO_VALUE` if *value* was
            :py:data:`~dogpile.cache.api.NO_VALUE`, or a
            :py:class:`~dogpile.cache.api.CachedValue`.
        """
        if value is NO_VALUE:
            return NO_VALUE
        if value.startswith('\0'):
            value = zlib.decompress(value[1:])
        payload, metadata = json.loads(value)
        return CachedValue(payload, metadata)

    def get(self, key):
        """
        Proxy a ``get`` call.

        The data returned from the proxied backend is loaded with
        :py:meth:`.load` before being returned.

        Parameters:
            key: A :term:`native string`.

        Returns:
            See the :py:meth:`.load` method.
        """
        return self.load(self.proxied.get(key))

    def get_multi(self, keys):
        """
        Proxy a ``get_multi`` call.

        The data returned from the proxied backend is loaded with
        :py:meth:`.load` before being returned.

        Parameters
            key (list): A list of :term:`native string` objects.

        Returns:
            list: See :py:meth:`.load` for the contents of the list.
        """
        return map(self.load, self.proxied.get_multi(keys))

    def save(self, value):
        """
        Serialize some data to JSON.

        If the serialized JSON data exceeds a megabyte, it is compressed before
        being returned. To indicate compressed data, a single NUL byte is
        prepended to the data.

        Parameters:
            value: A :py:class:`~dogpile.cache.api.CachedValue`.

        Returns:
            :term:`bytes`.
        """
        ret = [value.payload, value.metadata]
        ret = json.dumps(ret)
        if len(ret) > _GZIP_THRESHOLD:
            ret = '\0' + zlib.compress(ret)
            if len(ret) > _GZIP_THRESHOLD:
                raise ValueError('compressed object still too large')
        return ret

    def set(self, key, value):
        """
        Proxy a ``set`` call.

        The data sent to the proxied backend is first saved with
        :py:meth:`.save`.

        Parameters:
            key: A :term:`native string`.
            value: A :py:class:`~dogpile.cache.api.CachedValue`.
        """
        self.proxied.set(key, self.save(value))

    def set_multi(self, pairs):
        """
        Proxy a ``set_multi`` call.

        The data sent to the proxied backend is first saved with
        :py:meth:`.save`.

        Parameters
            pairs (dict): A mapping from :term:`native string` objects to
                :py:class:`~dogpile.cache.api.CachedValue` objects.
        """
        self.proxied.set_multi({k: self.save(v) for k, v in pairs.items()})

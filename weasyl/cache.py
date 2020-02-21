from __future__ import absolute_import

import functools
import time

from dogpile.cache.proxy import ProxyBackend
from pyramid.threadlocal import get_current_request


def _increments(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        start = time.time()
        result = func(self, *args, **kwargs)
        end = time.time()

        request = get_current_request()
        if hasattr(request, 'memcached_times'):
            request.memcached_times.append(end - start)
        if hasattr(request, 'query_debug'):
            query = '%s(%s)' % (
                func.__name__,
                ', '.join(map(repr, args) + ['%s=%r' % kv for kv in kwargs.items()]),
            )

            request.query_debug.append((query, end - start))

        return result

    return wrapper


class RequestMemcachedStats(ProxyBackend):
    @_increments
    def delete(self, key):
        self.proxied.delete(key)

    @_increments
    def delete_multi(self, keys):
        self.proxied.delete_multi(keys)

    @_increments
    def get(self, key):
        return self.proxied.get(key)

    @_increments
    def get_multi(self, keys):
        return self.proxied.get_multi(keys)

    @_increments
    def set(self, key, value):
        self.proxied.set(key, value)

    @_increments
    def set_multi(self, mapping):
        self.proxied.set_multi(mapping)

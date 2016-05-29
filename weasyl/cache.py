import time

from crochet import ReactorStopped, TimeoutError
from dogpile.cache.api import CacheBackend, NO_VALUE
from dogpile.cache import register_backend
from txyam.client import YamClient
from txyam.sync import SynchronousYamClient
import web

from libweasyl.cache import region


MEMCACHED_FAILURE_EXCEPTIONS = ReactorStopped, TimeoutError


class YamBackend(CacheBackend):
    def __init__(self, arguments):
        self.client = SynchronousYamClient(
            YamClient(arguments.pop('reactor'), arguments.pop('url'),
                      **arguments))
        self.client.yamClient.connect()

    def get(self, key):
        start = time.time()
        try:
            value = self.client.operation('get', key)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            return NO_VALUE
        delta = time.time() - start
        if hasattr(web.ctx, 'memcached_times'):
            web.ctx.memcached_times.append(delta)
        if value is None or value[1] is None:
            return NO_VALUE
        return value[1]

    def get_multi(self, keys):
        start = time.time()
        try:
            values = self.client.operation('getMultiple', keys)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            return [NO_VALUE] * len(keys)
        delta = time.time() - start
        if hasattr(web.ctx, 'memcached_times'):
            web.ctx.memcached_times.append(delta)
        ret = []
        for key in keys:
            value = values.get(key)
            if value is None or value[1] is None:
                ret.append(NO_VALUE)
            else:
                ret.append(value[1])
        return ret

    def set(self, key, value):
        try:
            self.client.async_operation('set', key, value)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            pass

    def set_multi(self, items):
        try:
            self.client.async_operation('setMultiple', items)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            pass

    def delete(self, key):
        try:
            self.client.async_operation('delete', key)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            pass

    def delete_multi(self, keys):
        try:
            self.client.async_operation('deleteMultiple', keys)
        except MEMCACHED_FAILURE_EXCEPTIONS:
            pass


register_backend('txyam', 'weasyl.cache', 'YamBackend')


__all__ = ['region']

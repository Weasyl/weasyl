import functools
import threading
import time

from prometheus_client import Histogram


_MEMCACHED_BUCKETS = [0.001, 0.005, 0.01, 0.025]


class MemcachedHistogram:
    def __init__(self, name, documentation, *args, **kwargs):
        self._state = threading.local()
        self._cached = Histogram(f"{name}_cached", f"{documentation} (cached)", *args, buckets=_MEMCACHED_BUCKETS, **kwargs)
        self._uncached = Histogram(f"{name}_uncached", f"{documentation} (uncached)", *args, **kwargs)

    def cached(self, func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            self._state.cached = True

            start = time.perf_counter()
            ret = func(*args, **kwargs)

            if self._state.cached:
                self._cached.observe(time.perf_counter() - start)

            return ret

        return wrapped

    def uncached(self, func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            self._state.cached = False

            start = time.perf_counter()
            ret = func(*args, **kwargs)
            self._uncached.observe(time.perf_counter() - start)

            return ret

        return wrapped

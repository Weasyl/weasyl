import functools
import threading
import time

from pyramid.threadlocal import get_current_request


class CachedMetric:
    """
    A metric for a cached operation. Adds a `cached` label.
    """

    def __init__(self, metric):
        self._state = threading.local()
        self._metric = metric
        metric.labels(cached="no")
        metric.labels(cached="yes")

    def cached(self, func):
        state = self._state
        metric = self._metric

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            state.cached = True

            start = time.perf_counter()
            ret = func(*args, **kwargs)
            duration = time.perf_counter() - start

            metric.labels(cached="yes" if state.cached else "no").observe(duration)

            return ret

        return wrapped

    def uncached(self, func):
        state = self._state

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            state.cached = False
            return func(*args, **kwargs)

        return wrapped


def separate_timing(func):
    """
    Exclude the timing information for a function that runs during request processing from the overall request’s metrics, allowing them to be recorded separately.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        request = get_current_request()

        outer_sql_times = request.sql_times
        outer_memcached_times = request.memcached_times
        request.sql_times = []
        request.memcached_times = []

        start = time.perf_counter()
        ret = func(*args, **kwargs)
        duration = time.perf_counter() - start

        request.sql_times = outer_sql_times
        request.memcached_times = outer_memcached_times
        request.excluded_time += duration

        return ret

    return wrapped

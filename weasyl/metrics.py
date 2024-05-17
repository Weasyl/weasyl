import functools
import threading
import time


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

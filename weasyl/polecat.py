"""Polecats are twisted weasyls.

Just bear with me here.
"""

from __future__ import absolute_import, division

import time

from twisted.application.service import Service
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.python import log
from twisted.web.server import Site


class WeasylSite(Site):
    def log(self, request):
        "Do nothing; we don't need request logging."

    def getResourceFor(self, request):
        resource = Site.getResourceFor(self, request)
        now = time.time()
        request.requestHeaders.addRawHeader('X-Request-Started-At', '%0.8f' % now)
        return resource


class PeriodicTasksService(Service):
    def __init__(self, clock, taskFunction, interval=60):
        self.clock = clock
        self.taskFunction = taskFunction
        self.interval = interval
        self._delayedCall = None
        self._looper = None
        self._loopFinished = None

    def startService(self):
        Service.startService(self)
        now = time.time()
        startDelta = now // self.interval * self.interval + self.interval - now
        self._delayedCall = self.clock.callLater(startDelta, self._startLooping)

    def _startLooping(self):
        self._delayedCall = None
        self._looper = LoopingCall(self._call)
        self._looper.clock = self.clock
        self._loopFinished = self._looper.start(self.interval)

    def _call(self):
        d = deferToThread(self.taskFunction)
        d.addErrback(log.err, "error calling periodic tasks")
        return d

    def stopService(self):
        if self._delayedCall:
            self._delayedCall.cancel()
            self._delayedCall = None
            return
        self._looper.stop()
        self._loopFinished.addCallback(lambda _: Service.stopService(self))
        return self._loopFinished

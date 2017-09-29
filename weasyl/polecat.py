"""Polecats are twisted weasyls.

Just bear with me here.
"""

from __future__ import absolute_import, division

import os
import time

import anyjson as json

from bisect import bisect_left
from twisted.application.internet import TimerService
from twisted.application.service import Service
from twisted.internet.protocol import DatagramProtocol, Factory
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.internet import defer
from twisted.protocols import amp
from twisted.python import log
from twisted.web.http import HTTPChannel, INTERNAL_SERVER_ERROR
from twisted.web.resource import ForbiddenResource, Resource
from twisted.web.server import Request, Site
from twisted.web.static import File

from weasyl import macro as m


def percentile(sorted_data, percentile):
    index = int((len(sorted_data) - 1) * (percentile / 100))
    return sorted_data[index]


def average(data):
    return sum(data) / len(data)


class WeasylRequest(Request):
    def getClientIP(self):
        "If there's an X-Forwarded-For, treat that as the client IP."
        forwarded_for = self.getHeader('x-forwarded-for')
        if forwarded_for is not None:
            return forwarded_for
        else:
            return Request.getClientIP(self)


class WeasylHTTPChannel(HTTPChannel):
    def connectionMade(self):
        self.site.gotClient()
        HTTPChannel.connectionMade(self)

    def connectionLost(self, reason):
        self.site.lostClient()
        HTTPChannel.connectionLost(self, reason)


class WeasylSite(Site):
    requestFactory = WeasylRequest
    protocol = WeasylHTTPChannel
    metrics = None

    requestCount = 0
    errorCount = 0
    activeClients = 0
    mostActiveClients = 0
    _clientsStoppedDeferred = None

    def __init__(self, *a, **kw):
        Site.__init__(self, *a, **kw)
        self.requestLengths = []
        self._activeRequests = set()

    def log(self, request):
        "Do nothing but increment the request count; we don't need request logging."
        self.requestCount += 1
        if self.metrics:
            self.metrics.increment('requests')
        if request.code == INTERNAL_SERVER_ERROR:
            self.errorCount += 1
            if self.metrics:
                self.metrics.increment('errors')

    def readRequestCount(self):
        "Return and reset the request count, request error percentage, and maximum active client count."
        errorPercentage = 0
        if self.requestCount:
            errorPercentage = self.errorCount / self.requestCount * 100
        ret = self.requestCount, errorPercentage, self.mostActiveClients
        self.requestCount = self.errorCount = 0
        self.mostActiveClients = self.activeClients
        return ret

    def readRequestLengths(self):
        "Return and reset the request lengths."
        ret, self.requestLengths = self.requestLengths, []
        return ret

    def getResourceFor(self, request):
        "Fetch a resource and measure the time until it's finished writing."
        resource = Site.getResourceFor(self, request)
        now = time.time()
        request.requestHeaders.addRawHeader('X-Request-Started-At', '%0.8f' % now)
        request.notifyFinish().addBoth(self._recordRequestTime, now, request)
        self._activeRequests.add(request)
        return resource

    def _recordRequestTime(self, ign, startedAt, request):
        delta = time.time() - startedAt
        self.requestLengths.append(delta)
        self._activeRequests.discard(request)

    def gotClient(self):
        "A new client has connected."
        self.activeClients += 1
        self.mostActiveClients = max(self.mostActiveClients, self.activeClients)

    def lostClient(self):
        "A client has disconnected."
        self.activeClients -= 1
        if not self.activeClients and self._clientsStoppedDeferred:
            self._clientsStoppedDeferred.callback(None)

    def gracefullyStopActiveClients(self):
        "Returns a Deferred that fires when all clients have disconnected."
        if not self.activeClients:
            return defer.succeed(None)
        for request in self._activeRequests:
            request.setHeader('connection', 'close')
        self._clientsStoppedDeferred = defer.Deferred()
        return self._clientsStoppedDeferred


class TryChildrenBeforeLeaf(Resource):
    "A Resource given a leaf resource tried after all of the put children."

    def __init__(self, leaf):
        Resource.__init__(self)
        self.leaf = leaf

    def getChild(self, child, request):
        "getChildWithDefault failed, so delegate to our leaf."
        request.postpath.insert(0, request.prepath.pop())
        return self.leaf

    def render(self, request):
        "Delegate requests to the root to the leaf as well."
        return self.leaf.render(request)


def rewriteSubmissionUploads(request):
    """Rewrite submission uploads to remove the artist name from the URL.

    This is for symmetry with the nginx config, which does mostly the same
    thing. The equivalent nginx rewrite rule is:

    rewrite "^(/static/(submission|character)/../../../../../../)(.+)-(.+)$" $1$4 break;
    """

    if (request.postpath[0] == 'static' and
            request.postpath[1] in ('submission', 'character') and
            '-' in request.postpath[-1]):
        _, _, request.postpath[-1] = request.postpath[-1].rpartition('-')
        request.path = '/' + '/'.join(request.prepath + request.postpath)


def rewriteNonlocalImages(request):
    """Rewrite static files to be fetched from the live site if they don't exist
    locally.

    This is convenient for people working off of database dumps of the live
    site, so the images aren't all hella broken.
    """

    if request.postpath[0] != 'static':
        return
    localPath = os.path.join(m.MACRO_STORAGE_ROOT, request.path.lstrip('/'))
    if os.path.exists(localPath):
        return
    request.postpath[0] = '_weasyl_static'
    request.path = '/' + '/'.join(request.prepath + request.postpath)


class FetchRequestStats(amp.Command):
    "A command to request request statistics from a running weasyl backend."
    arguments = []
    response = [
        ('requestCount', amp.Integer()),
        ('errorPercentage', amp.Float()),
        ('mostActiveClients', amp.Integer()),
    ]


class FetchRequestLengthStats(amp.Command):
    "A command to request request length statistics from a running weasyl backend."
    arguments = [
        ('percentiles', amp.ListOf(amp.Integer())),
        ('lengths', amp.ListOf(amp.Float())),
    ]
    response = [
        ('lengths', amp.ListOf(amp.Float(), optional=True)),
        ('percentiles', amp.ListOf(amp.Float(), optional=True)),
    ]


class FetchRequestBreakdownStats(amp.Command):
    "A command to request request breakdown statistics from a running weasyl backend."
    arguments = [
        ('percentiles', amp.ListOf(amp.Integer())),
    ]
    response = [
        ('averageTimeQueued', amp.Float(optional=True)),
        ('averageTimeInSQL', amp.Float(optional=True)),
        ('averageTimeInMemcached', amp.Float(optional=True)),
        ('averageTimeInPython', amp.Float(optional=True)),
        ('totalTimeQueued', amp.Float(optional=True)),
        ('totalTimeInSQL', amp.Float(optional=True)),
        ('totalTimeInMemcached', amp.Float(optional=True)),
        ('totalTimeInPython', amp.Float(optional=True)),
        ('queries', amp.ListOf(amp.Float(), optional=True)),
    ]


class FetchThreadPoolStats(amp.Command):
    "A command to request thread pool statistics from a running weasyl backend."
    arguments = []
    response = [
        ('threadsWaiting', amp.Integer()),
        ('threadsWorking', amp.Integer()),
        ('workerQueueSize', amp.Integer()),
    ]


class WeasylSiteStats(amp.AMP):
    @FetchRequestStats.responder
    def fetchRequestStats(self):
        requestCount, errorPercentage, mostActiveClients = self.factory.site.readRequestCount()
        return dict(
            requestCount=requestCount,
            errorPercentage=errorPercentage,
            mostActiveClients=mostActiveClients,
        )

    @FetchRequestLengthStats.responder
    def fetchRequestLengthStats(self, percentiles, lengths):
        requestLengths = self.factory.site.readRequestLengths()
        if not requestLengths:
            return {}
        requestLengths.sort()
        denom = len(requestLengths) / 100
        return dict(
            lengths=[percentile(requestLengths, p) for p in percentiles],
            percentiles=[
                bisect_left(requestLengths, l) / denom for l in lengths],
        )

    @FetchRequestBreakdownStats.responder
    def fetchRequestBreakdownStats(self, percentiles):
        if not self.factory.timings:
            return {}
        queued, sql, memcached, python, queries, memcached_queries = zip(*self.factory.timings)
        self.factory.timings = []
        queries = sorted(queries)
        return dict(
            averageTimeQueued=average(queued),
            averageTimeInSQL=average(sql),
            averageTimeInMemcached=average(memcached),
            averageTimeInPython=average(python),
            totalTimeQueued=sum(queued),
            totalTimeInSQL=sum(sql),
            totalTimeInMemcached=sum(memcached),
            totalTimeInPython=sum(python),
            queries=[percentile(queries, p) for p in percentiles],
        )

    @FetchThreadPoolStats.responder
    def fetchThreadPoolStats(self):
        pool = self.factory.threadPool
        return dict(
            threadsWaiting=len(pool.waiters),
            threadsWorking=len(pool.working),
            workerQueueSize=pool.q.qsize(),
        )

    def makeConnection(self, transport):
        "Upcall to avoid noisy logging messages on connection open."
        amp.BinaryBoxProtocol.makeConnection(self, transport)

    def connectionLost(self, reason):
        "Upcall to avoid noisy logging messages on connection close."
        amp.BinaryBoxProtocol.connectionLost(self, reason)
        self.transport = None


class WeasylSiteStatsFactory(Factory):
    protocol = WeasylSiteStats
    noisy = False

    def __init__(self, site, threadPool, reactor, requestLogHost=None):
        self.site = site
        self.threadPool = threadPool
        self.timings = []
        self.reactor = reactor
        self.requestLogger = None
        if requestLogHost is not None:
            host, port = requestLogHost
            d = self.reactor.resolve(host)
            d.addCallback(self._gotRequestLoggerHost, port)
            d.addErrback(log.err, 'error resolving request logger host')

    def _gotRequestLoggerHost(self, host, port):
        self.requestLogger = DatagramProtocol()
        self.reactor.listenUDP(0, self.requestLogger)
        self.requestLogger.transport.connect(host, port)

    def _logRequest(self, queued, sql, memcached, python, queries, memcached_queries,
                    userid, sessionid, method, endpoint, endpoint_args):
        self.timings.append((queued, sql, memcached, python, queries, memcached_queries))
        if self.site.metrics:
            metrics = self.site.metrics
            metrics.timing('queued', queued)
            metrics.timing('sql', sql)
            metrics.timing('memcached', memcached)
            metrics.timing('python', python)
        if self.requestLogger:
            self.requestLogger.transport.write(json.dumps({
                'time_queued': queued,
                'time_in_sql': sql,
                'time_in_memcached': memcached,
                'time_in_python': python,
                'sql_queries': queries,
                'memcached_queries': memcached_queries,
                'userid': userid,
                'sessionid': sessionid,
                'endpoint': endpoint,
                'endpoint_args': endpoint_args,
                'method': method,
            }))

    def logRequest(self, *a, **kw):
        self.reactor.callFromThread(self._logRequest, *a, **kw)

    def _metric(self, name, *a, **kw):
        getattr(self.site.metrics, name)(*a, **kw)

    def metric(self, *a, **kw):
        if not self.site.metrics:
            return
        self.reactor.callFromThread(self._metric, *a, **kw)

    def _periodicMetrics(self):
        metrics = self.site.metrics
        metrics.gauge('threadswaiting', len(self.threadPool.waiters))
        metrics.gauge('threadsworking', len(self.threadPool.working))
        metrics.gauge('queuesize', self.threadPool.q.qsize())

    def metricService(self):
        return TimerService(10, self._periodicMetrics)


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


class NoDirectoryListingFile(File):
    def directoryListing(self):
        return ForbiddenResource()

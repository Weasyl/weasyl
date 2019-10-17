#!/usr/bin/env python
#%# family=auto
#%# capabilities=autoconf suggest



import os

from twisted.internet.endpoints import clientFromString
from twisted.internet import defer, task, protocol
from twisted.protocols import amp

from weasyl import polecat

PERCENTILES = [0, 50, 85, 95, 98, 100]
LENGTHS = [0.1, 0.5, 1, 2, 5]


def labelify(x):
    return str(x).replace('.', '_')


pluginClasses = []


def addPlugin(cls):
    # makes a class attribute instead of a metaclass attribute.
    cls.name = cls.__name__
    pluginClasses.append(cls)
    return cls


@addPlugin
class weasyl_request(object):
    def __init__(self, endpoints):
        self.endpoints = endpoints

    def suggest(self):
        return ['']

    @defer.inlineCallbacks
    def fetchStats(self, endpoint):
        amp = yield endpoint.connect(AMPFactory())
        stats = yield amp.callRemote(polecat.FetchRequestStats)
        defer.returnValue(stats)

    @defer.inlineCallbacks
    def command_fetch(self, ignored):
        names, endpoints = list(zip(*iter(self.endpoints.items())))
        results = yield defer.DeferredList(
            [self.fetchStats(endpoint) for endpoint in endpoints],
            consumeErrors=True)
        resultsByParameter = {}
        for name, (success, stats) in zip(names, results):
            if not success:
                continue
            for k, v in stats.items():
                resultsByParameter.setdefault(k, {})[name] = v

        print('multigraph weasyl_request')
        for name, v in resultsByParameter['requestCount'].items():
            print('requestCount_%s.value %s' % (name, v))

        print('multigraph weasyl_error_percentage')
        for name, v in resultsByParameter['errorPercentage'].items():
            print('errorPercentage_%s.value %s' % (name, v))

        print('multigraph weasyl_max_active_clients')
        for name, v in resultsByParameter['mostActiveClients'].items():
            print('mostActiveClients_%s.value %s' % (name, v))

    def command_config(self, ignored):
        print("""
multigraph weasyl_request
graph_title Weasyl requests
graph_category weasyl
graph_args --base 1000
graph_vlabel Requests per second
""")

        for name in sorted(self.endpoints):
            print("""
requestCount_{0}.type ABSOLUTE
requestCount_{0}.min 0
requestCount_{0}.draw LINESTACK2
requestCount_{0}.label {0} requests
requestCount_{0}.info The number of requests to the weasyl backend
""".format(name))

        print("""
multigraph weasyl_error_percentage
graph_title Weasyl request error percentage
graph_category weasyl
graph_args --base 1000
graph_vlabel request error %
""")

        for name in sorted(self.endpoints):
            print("""
errorPercentage_{0}.type ABSOLUTE
errorPercentage_{0}.min 0
errorPercentage_{0}.max 100
errorPercentage_{0}.draw LINE2
errorPercentage_{0}.label {0} request error percentage
errorPercentage_{0}.info What percentage of requests resulted in an error
""".format(name))

        print("""
multigraph weasyl_max_active_clients
graph_title Weasyl maximum simultaneous clients
graph_category weasyl
graph_args --base 1000
graph_vlabel simultaneous clients
""")

        for name in sorted(self.endpoints):
            print("""
mostActiveClients_{0}.type GAUGE
mostActiveClients_{0}.min 0
mostActiveClients_{0}.draw LINE2
mostActiveClients_{0}.label {0} simultaneous clients
mostActiveClients_{0}.info The most simultaneous clients over the last period
""".format(name))


class PerEndpointPluginBase(object):
    command = None

    def __init__(self, endpoints):
        self.endpoints = endpoints

    def _ensureEndpoint(self, name):
        if name not in self.endpoints:
            raise ValueError("%r is not a known client" % (name,))

    def suggest(self):
        return self.endpoints

    @defer.inlineCallbacks
    def command_fetch(self, endpointName):
        self._ensureEndpoint(endpointName)
        endpoint = self.endpoints[endpointName]
        amp = yield endpoint.connect(AMPFactory())
        stats = yield self.fetchStats(amp)
        self.formatStats(stats, endpointName)

    def fetchStats(self, amp):
        return amp.callRemote(self.command)

    def formatStats(self, stats, endpointName):
        for k, v in stats.items():
            if v is None:
                v = 'U'
            print('%s.value %s' % (k, v))


@addPlugin
class weasyl_request_length_(PerEndpointPluginBase):
    command = polecat.FetchRequestLengthStats

    def fetchStats(self, amp):
        return amp.callRemote(
            self.command, percentiles=PERCENTILES, lengths=LENGTHS)

    def formatStats(self, stats, endpointName):
        if stats['lengths'] is not None:
            print('multigraph weasyl_request_length_%s' % endpointName)
            for p, v in zip(PERCENTILES, stats['lengths']):
                print('percentile_%s.value %s' % (p, v))

        if stats['percentiles'] is not None:
            print('multigraph weasyl_request_percentile_%s' % endpointName)
            for l, v in zip(LENGTHS, stats['percentiles']):
                print('length_%s.value %s' % (labelify(l), v))

    def command_config(self, endpointName):
        self._ensureEndpoint(endpointName)
        print("""
multigraph weasyl_request_length_{0}
graph_title {0} request processing length
graph_category weasyl
graph_args --base 1000 -l 0
graph_vlabel s
""".format(endpointName))

        for p in PERCENTILES:
            print("""
percentile_{0}.type GAUGE
percentile_{0}.min 0
percentile_{0}.label {0}th percentile request length
percentile_{0}.info The {0}th percentile of time taken processing the request since the last poll
""".format(p))

        print("""
multigraph weasyl_request_percentile_{0}
graph_title {0} percentile of request processing length
graph_category weasyl
graph_args --base 1000 -u 100 --rigid
graph_vlabel percentile
""".format(endpointName))

        for l in LENGTHS:
            print("""
length_{0}.type GAUGE
length_{0}.min 0
length_{0}.max 100
length_{0}.label percentile of {1}s request
length_{0}.info The percentile of a {1}s request during the last poll interval
""".format(labelify(l), l))


@addPlugin
class weasyl_threadpool_(PerEndpointPluginBase):
    command = polecat.FetchThreadPoolStats

    def command_config(self, endpointName):
        self._ensureEndpoint(endpointName)
        print("""
graph_title {0} thread pool
graph_category weasyl
graph_args --base 1000 -l 0
graph_vlabel Number of threads
graph_order threadsWaiting threadsWorking workerQueueSize
threadsWaiting.type GAUGE
threadsWaiting.min 0
threadsWaiting.draw AREASTACK
threadsWaiting.label threads waiting
threadsWaiting.info The number of threads waiting for work
threadsWorking.type GAUGE
threadsWorking.min 0
threadsWorking.draw AREASTACK
threadsWorking.label threads working
threadsWorking.info The number of threads doing work
workerQueueSize.type GAUGE
workerQueueSize.min 0
workerQueueSize.draw AREASTACK
workerQueueSize.label jobs pending
workerQueueSize.info The number of jobs waiting for a free thread
""".format(endpointName))


@addPlugin
class weasyl_request_breakdown_(PerEndpointPluginBase):
    command = polecat.FetchRequestBreakdownStats

    def fetchStats(self, amp):
        return amp.callRemote(self.command, percentiles=PERCENTILES)

    def formatStats(self, stats, endpointName):
        print('multigraph weasyl_request_breakdown_queries_%s' % endpointName)
        queries = stats.pop('queries', None)
        if queries is not None:
            for p, v in zip(PERCENTILES, queries):
                print('percentile_%s.value %s' % (labelify(p), v))

        print('multigraph weasyl_request_breakdown_length_averages_%s' % endpointName)
        super(weasyl_request_breakdown_, self).formatStats(
            {k: v for k, v in stats.items() if k.startswith('average')}, endpointName)

        print('multigraph weasyl_request_breakdown_length_totals_%s' % endpointName)
        super(weasyl_request_breakdown_, self).formatStats(
            {k: v for k, v in stats.items() if k.startswith('total')}, endpointName)

    def command_config(self, endpointName):
        self._ensureEndpoint(endpointName)

        print("""
multigraph weasyl_request_breakdown_length_averages_{0}
graph_title {0} request processing length average breakdown
graph_category weasyl
graph_args --base 1000 -l 0
graph_vlabel s
averageTimeQueued.type GAUGE
averageTimeQueued.min 0
averageTimeQueued.draw AREASTACK
averageTimeQueued.label average time queued
averageTimeQueued.info The average time spent before a request was processed since the last poll
averageTimeInSQL.type GAUGE
averageTimeInSQL.min 0
averageTimeInSQL.draw AREASTACK
averageTimeInSQL.label average time in SQL
averageTimeInSQL.info The average time spent running SQL queries since the last poll
averageTimeInMemcached.type GAUGE
averageTimeInMemcached.min 0
averageTimeInMemcached.draw AREASTACK
averageTimeInMemcached.label average time in memcached
averageTimeInMemcached.info The average time spent running memcached queries since the last poll
averageTimeInPython.type GAUGE
averageTimeInPython.min 0
averageTimeInPython.draw AREASTACK
averageTimeInPython.label average time in python
averageTimeInPython.info The average time spent running python code since the last poll
""".format(endpointName))

        print("""
multigraph weasyl_request_breakdown_length_totals_{0}
graph_title {0} request processing length total breakdown
graph_category weasyl
graph_args --base 1000 -l 0
graph_vlabel s
totalTimeQueued.type GAUGE
totalTimeQueued.min 0
totalTimeQueued.draw AREASTACK
totalTimeQueued.label total time queued
totalTimeQueued.info The total time spent before a request was processed since the last poll
totalTimeInSQL.type GAUGE
totalTimeInSQL.min 0
totalTimeInSQL.draw AREASTACK
totalTimeInSQL.label total time in SQL
totalTimeInSQL.info The total time spent running SQL queries since the last poll
totalTimeInMemcached.type GAUGE
totalTimeInMemcached.min 0
totalTimeInMemcached.draw AREASTACK
totalTimeInMemcached.label total time in memcached
totalTimeInMemcached.info The total time spent running memcached queries since the last poll
totalTimeInPython.type GAUGE
totalTimeInPython.min 0
totalTimeInPython.draw AREASTACK
totalTimeInPython.label total time in python
totalTimeInPython.info The total time spent running python code since the last poll
""".format(endpointName))

        print("""
multigraph weasyl_request_breakdown_queries_{0}
graph_title {0} number of queries
graph_category weasyl
graph_args --base 1000 -l 0
graph_vlabel queries
""".format(endpointName))

        for p in PERCENTILES:
            print("""
percentile_{0}.type GAUGE
percentile_{0}.min 0
percentile_{0}.label {0}th percentile number of queries
percentile_{0}.info The {0}th percentile of number of queries executed per request since the last poll
""".format(p))


class AMPFactory(protocol.ClientFactory):
    protocol = amp.AMP


def nameLength(cls):
    return len(cls.__name__)


def main(reactor, procName, *args):
    procName = os.path.basename(procName)

    clientEndpoints = {}
    for k, v in os.environ.items():
        _, _, clientName = k.partition('client_endpoint_')
        if clientName:
            clientEndpoints[clientName] = clientFromString(reactor, v)
    if not clientEndpoints:
        raise ValueError("no client endpoints detected in the environment")

    plugins = [pluginClass(clientEndpoints)
               for pluginClass in sorted(pluginClasses, key=nameLength, reverse=True)]

    if args == ('autoconf',):
        print('yes')
        return defer.succeed(None)

    if args == ('suggest',):
        suggestions = []
        for plugin in plugins:
            suggestions.extend((plugin.name + arg).partition(procName)[2]
                               for arg in plugin.suggest())
        print('\n'.join(suggestion for suggestion in suggestions if suggestion))
        return defer.succeed(None)

    for plugin in plugins:
        _, foundPluginName, arg = procName.partition(plugin.name)
        if not foundPluginName:
            continue
        command = 'fetch' if not args else args[0]
        method = getattr(plugin, 'command_' + command, None)
        if not method:
            raise ValueError("%r plugin can't handle the command %r" % (plugin.name, command))
        return defer.maybeDeferred(method, arg)

    raise ValueError("no plugin was found with the name %r" % (procName,))


if __name__ == "__main__":
    import sys
    task.react(main, sys.argv)

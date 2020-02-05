# -*- python -*-
import os

import crochet
from twisted.application.internet import StreamServerEndpointService
from twisted.application import service
from twisted.internet import reactor, endpoints
from twisted.web.resource import NoResource
from twisted.web.wsgi import WSGIResource

import weasyl.polecat
import weasyl.wsgi
import weasyl.define as d
import weasyl.macro as m
from libweasyl import cache

threadPool = reactor.getThreadPool()

configuredMaxThreads = os.environ.get('WEASYL_MAX_THREAD_POOL_SIZE')
if configuredMaxThreads is not None:
    threadPool.adjustPoolsize(
        maxthreads=int(configuredMaxThreads),
    )

weasylResource = WSGIResource(reactor, threadPool, weasyl.wsgi.wsgi_app)
if os.environ.get('WEASYL_SERVE_STATIC_FILES'):
    weasylResource = weasyl.polecat.TryChildrenBeforeLeaf(weasylResource)
    staticResource = weasyl.polecat.NoDirectoryListingFile(
        os.path.join(m.MACRO_APP_ROOT, 'static'))

    for childName in ["character", "media"]:
        childResource = weasyl.polecat.NoDirectoryListingFile(
            os.path.join(m.MACRO_STORAGE_ROOT, "static", childName))

        if os.environ.get('WEASYL_REDIRECT_MISSING_STATIC'):
            childResource = weasyl.polecat.RedirectIfNotFound(
                childResource,
                targetPrefix="https://cdn.weasyl.com/static/" + childName + "/",
                isNotFound=lambda r: isinstance(r, NoResource),
            )

        staticResource.putChild(childName, childResource)

    cssResource = weasyl.polecat.NoDirectoryListingFile(
        os.path.join(m.MACRO_APP_ROOT, 'build/css'))
    weasylResource.putChild('static', staticResource)
    weasylResource.putChild('css', cssResource)
    rewriters = [weasyl.polecat.rewriteCharacterUploads]

    from twisted.web.rewrite import RewriterResource
    weasylResource = RewriterResource(weasylResource, *rewriters)

requestLogHost = d.config_read_setting('request_log_host', section='backend')
if requestLogHost:
    requestLogHost, _, requestLogPort = requestLogHost.partition(':')
    requestLogPort = int(requestLogPort)
    requestLogHost = requestLogHost, requestLogPort
site = weasyl.polecat.WeasylSite(weasylResource)
siteStats = weasyl.polecat.WeasylSiteStatsFactory(site, threadPool, reactor, requestLogHost=requestLogHost)
weasyl.define.statsFactory = siteStats

application = service.Application('weasyl')
def attachServerEndpoint(factory, endpointEnvironKey, defaultString=None):
    "Generates a server endpoint from an environment variable and attaches it to the application."
    description = os.environ.get(endpointEnvironKey, defaultString)
    if not description:
        return
    endpoint = endpoints.serverFromString(reactor, description)
    StreamServerEndpointService(endpoint, factory).setServiceParent(application)

attachServerEndpoint(site, 'WEASYL_WEB_ENDPOINT', 'tcp:8080:interface=127.0.0.1')
attachServerEndpoint(siteStats, 'WEASYL_WEB_STATS_ENDPOINT', 'tcp:8267:interface=127.0.0.1')

if d.config_read_bool('run_periodic_tasks', section='backend'):
    from weasyl.cron import run_periodic_tasks
    weasyl.polecat.PeriodicTasksService(reactor, run_periodic_tasks).setServiceParent(application)

if not d.config_read_bool('rough_shutdowns', section='backend'):
    reactor.addSystemEventTrigger('before', 'shutdown', site.gracefullyStopActiveClients)


statsdServer = d.config_read_setting('server', section='statsd')
if statsdServer:
    statsdHost, _, statsdPort = statsdServer.rpartition(':')
    statsdPort = int(statsdPort)

    import socket

    from txstatsd.client import TwistedStatsDClient, StatsDClientProtocol
    from txstatsd.metrics.metrics import Metrics
    from txstatsd.report import ReportingService

    namespace = d.config_read_setting('namespace', section='statsd')
    if namespace is None:
        namespace = os.environ.get('WEASYL_STATSD_NAMESPACE')
    if namespace is None:
        namespace = socket.gethostname().split('.')[0]
    statsdClient = TwistedStatsDClient.create(statsdHost, statsdPort)
    site.metrics = Metrics(connection=statsdClient, namespace=namespace)

    reporting = ReportingService()
    reporting.setServiceParent(application)
    siteStats.metricService().setServiceParent(application)

    protocol = StatsDClientProtocol(statsdClient)
    reactor.listenUDP(0, protocol)


crochet.no_setup()


cache.region.configure(
    'txyam',
    arguments=dict(
        reactor=reactor,
        url=d.config_read_setting(
            'servers', 'tcp:127.0.0.1:11211', 'memcached').split(),
        retryDelay=10,
        timeOut=0.4,
    ),
    wrap=[cache.ThreadCacheProxy, cache.JSONProxy],
    replace_existing_backend=True
)

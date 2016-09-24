# -*- python -*-
import os

import crochet
from twisted.application.internet import StreamServerEndpointService
from twisted.application import service
from twisted.internet import reactor, endpoints
from twisted.web.wsgi import WSGIResource
from dozer import Dozer

import weasyl.polecat
import weasyl.wsgi
import weasyl.define as d
from libweasyl import cache

weasyl.wsgi.wsgi_app = Dozer(weasyl.wsgi.wsgi_app)

threadPool = reactor.getThreadPool()
threadPool.adjustPoolsize(minthreads=6, maxthreads=12)
weasylResource = WSGIResource(reactor, threadPool, weasyl.wsgi.wsgi_app)
if os.environ.get('WEASYL_SERVE_STATIC_FILES'):
    weasylResource = weasyl.polecat.TryChildrenBeforeLeaf(weasylResource)
    staticResource = weasyl.polecat.NoDirectoryListingFile(
        os.path.join(os.environ['WEASYL_ROOT'], 'static'))
    cssResource = weasyl.polecat.NoDirectoryListingFile(
        os.path.join(os.environ['WEASYL_ROOT'], 'build/css'))
    jsResource = weasyl.polecat.NoDirectoryListingFile(
        os.path.join(os.environ['WEASYL_ROOT'], 'build/js'))
    weasylResource.putChild('static', staticResource)
    weasylResource.putChild('css', cssResource)
    weasylResource.putChild('js', jsResource)
    rewriters = [weasyl.polecat.rewriteSubmissionUploads]

    if os.environ.get('WEASYL_REVERSE_PROXY_STATIC'):
        from twisted.web import proxy
        weasylResource.putChild(
            '_weasyl_static', proxy.ReverseProxyResource('www.weasyl.com', 80, '/static'))
        rewriters.append(weasyl.polecat.rewriteNonlocalImages)

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

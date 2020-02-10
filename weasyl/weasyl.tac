# -*- python -*-
import os

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

site = weasyl.polecat.WeasylSite(weasylResource)

application = service.Application('weasyl')
def attachServerEndpoint(factory, endpointEnvironKey, defaultString):
    "Generates a server endpoint from an environment variable and attaches it to the application."
    description = os.environ.get(endpointEnvironKey, defaultString)
    endpoint = endpoints.serverFromString(reactor, description)
    StreamServerEndpointService(endpoint, factory).setServiceParent(application)

attachServerEndpoint(site, 'WEASYL_WEB_ENDPOINT', 'tcp:8080:interface=127.0.0.1')

if d.config_read_bool('run_periodic_tasks', section='backend'):
    from weasyl.cron import run_periodic_tasks
    weasyl.polecat.PeriodicTasksService(reactor, run_periodic_tasks).setServiceParent(application)


cache.region.configure(
    'dogpile.cache.pylibmc',
    arguments={
        'url': d.config_read_setting('servers', "127.0.0.1", section='memcached').split(),
        'binary': True,
    },
    wrap=[cache.ThreadCacheProxy, cache.JSONProxy],
    replace_existing_backend=True
)

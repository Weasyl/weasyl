"""Polecats are twisted weasyls.

Just bear with me here.
"""

from __future__ import absolute_import, division

import time
import urllib

from twisted.application.service import Service
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.python import log
from twisted.python.components import proxyForInterface
from twisted.web.resource import IResource, ForbiddenResource, Resource
from twisted.web.server import Request, Site
from twisted.web.static import File
from twisted.web.util import Redirect


class WeasylRequest(Request):
    def getClientIP(self):
        "If there's an X-Forwarded-For, treat that as the client IP."
        forwarded_for = self.getHeader('x-forwarded-for')
        if forwarded_for is not None:
            return forwarded_for
        else:
            return Request.getClientIP(self)


class WeasylSite(Site):
    requestFactory = WeasylRequest

    def log(self, request):
        "Do nothing; we don't need request logging."

    def getResourceFor(self, request):
        resource = Site.getResourceFor(self, request)
        now = time.time()
        request.requestHeaders.addRawHeader('X-Request-Started-At', '%0.8f' % now)
        return resource


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


def rewriteCharacterUploads(request):
    """Rewrite character uploads to remove the artist name from the URL.

    This is for symmetry with the nginx config, which does mostly the same
    thing. The equivalent nginx rewrite rule is:

    rewrite "^(/static/character/../../../../../../)(.+)-(.+)$" $1$4 break;
    """
    if (
        len(request.postpath) == 9
        and request.postpath[0] == 'static'
        and request.postpath[1] == 'character'
        and '-' in request.postpath[8]
    ):
        _, _, request.postpath[8] = request.postpath[8].rpartition('-')
        request.path = '/' + '/'.join(request.prepath + request.postpath)


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


class RedirectIfNotFound(proxyForInterface(IResource)):
    """
    Redirects not-found responses from any descendant resources to some
    different URL prefix.

    The prefix is joined to the remaining path with simple string
    concatenation; it should end with a trailing slash.

    `isNotFound` is called to determine whether a resource is considered a
    not-found response.
    """

    def __init__(self, original, targetPrefix, isNotFound):
        super(RedirectIfNotFound, self).__init__(original)
        self.targetPrefix = targetPrefix
        self.isNotFound = isNotFound

    def getChildWithDefault(self, child, request):
        ret = self.original.getChildWithDefault(child, request)
        quotedChild = urllib.quote(child, safe="")

        if self.isNotFound(ret):
            # https://github.com/twisted/twisted/blob/twisted-19.10.0/src/twisted/web/server.py#L222
            encoded_postpath = [quotedChild]
            encoded_postpath.extend(urllib.quote(segment, safe="") for segment in request.postpath)

            return Redirect(self.targetPrefix + "/".join(encoded_postpath))

        return RedirectIfNotFound(
            ret,
            targetPrefix=self.targetPrefix + quotedChild + "/",
            isNotFound=self.isNotFound,
        )

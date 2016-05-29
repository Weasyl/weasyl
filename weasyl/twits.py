# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

"I HATE TWITTER"
from __future__ import absolute_import

from twisted.web.http_headers import Headers
from twisted.internet.error import ConnectionDone, ConnectionLost
from twisted.web.client import ResponseDone, ResponseFailed
from twisted.web.http import PotentialDataLoss
from twisted.internet import defer, protocol
import oauth2

import urlparse
import urllib
import json

from weasyl import define

defaultSignature = oauth2.SignatureMethod_HMAC_SHA1()
defaultTwitterAPI = 'https://api.twitter.com/1.1/'


class StringReceiver(protocol.Protocol):
    def __init__(self, byteLimit=None):
        self.bytesRemaining = byteLimit
        self.deferred = defer.Deferred()
        self._buffer = []

    def dataReceived(self, data):
        data = data[:self.bytesRemaining]
        self._buffer.append(data)
        if self.bytesRemaining is not None:
            self.bytesRemaining -= len(data)
            if not self.bytesRemaining:
                self.transport.stopProducing()

    def connectionLost(self, reason):
        connection_lost = (
            reason.check(ResponseFailed) and
            any(exn.check(ConnectionDone, ConnectionLost)
                for exn in reason.value.reasons))

        if connection_lost or reason.check(ResponseDone, PotentialDataLoss):
            self.deferred.callback(''.join(self._buffer))
        else:
            self.deferred.errback(reason)


def receive(response, receiver):
    response.deliverBody(receiver)
    return receiver.deferred


class UnexpectedHTTPStatus(Exception):
    pass


def trapBadStatuses(response, goodStatuses=(200,)):
    if response.code not in goodStatuses:
        raise UnexpectedHTTPStatus(response.code, response.phrase)
    return response


class OAuthAgent(object):
    "An Agent wrapper that adds OAuth authorization headers."
    def __init__(self, agent, consumer, token, signatureMethod=defaultSignature):
        self.agent = agent
        self.consumer = consumer
        self.token = token
        self.signatureMethod = signatureMethod

    def request(self, method, uri, headers=None, bodyProducer=None, parameters=None, addAuthHeader=True):
        """Make a request, optionally signing it.

        Any query string passed in `uri` will get clobbered by the urlencoded
        version of `parameters`.
        """
        if headers is None:
            headers = Headers()
        if parameters is None:
            parameters = {}
        if addAuthHeader:
            req = oauth2.Request.from_consumer_and_token(
                self.consumer, token=self.token,
                http_method=method, http_url=uri, parameters=parameters)
            req.sign_request(self.signatureMethod, self.consumer, self.token)
            for header, value in req.to_header().iteritems():
                # oauth2, for some bozotic reason, gives unicode header values
                headers.addRawHeader(header, value.encode())
        parsed = urlparse.urlparse(uri)
        uri = urlparse.urlunparse(parsed._replace(query=urllib.urlencode(parameters)))
        return self.agent.request(method, uri, headers, bodyProducer)


class Twitter(object):
    "Close to the most minimal twitter interface ever."
    def __init__(self, agent, twitterAPI=defaultTwitterAPI):
        self.agent = agent
        self.twitterAPI = twitterAPI

    def _makeRequest(self, whichAPI, method, resource, parameters):
        d = self.agent.request(method, urlparse.urljoin(whichAPI, resource), parameters=parameters)
        d.addCallback(trapBadStatuses)
        return d

    def request(self, resource, method='GET', **parameters):
        """Make a request to the twitter 1.1 API.

        `resource` is the part of the resource URL not including the API URL,
        e.g. 'statuses/show.json'. As everything gets decoded by `json.loads`,
        this should always end in '.json'. Any parameters passed in as keyword
        arguments will be added to the URL as the query string. The `Deferred`
        returned will fire with the decoded JSON.
        """
        d = self._makeRequest(self.twitterAPI, method, resource, parameters)
        d.addCallback(receive, StringReceiver())
        d.addCallback(json.loads)
        return d


if define.config_obj.has_option('twitter', 'consumer_key'):
    from twisted.internet import reactor
    from twisted.python import log
    from twisted.web.client import Agent, HTTPConnectionPool

    consumer = oauth2.Consumer(
        define.config_obj.get('twitter', 'consumer_key'),
        define.config_obj.get('twitter', 'consumer_secret'))
    pool = HTTPConnectionPool(reactor)
    agent = Agent(reactor, pool=pool)

    def _post(account, message):
        token = oauth2.Token(
            define.config_obj.get('twitter-' + account, 'access_token'),
            define.config_obj.get('twitter-' + account, 'access_secret'))
        twits = Twitter(OAuthAgent(agent, consumer, token))
        d = twits.request('statuses/update.json', 'POST', status=message)
        d.addErrback(log.err, 'error posting %r to twitter' % (message,))

    def post(account, message):
        reactor.callFromThread(_post, account, message.encode('utf-8'))

else:
    def post(account, message):
        print "%s would've tweeted: %r" % (account, message)

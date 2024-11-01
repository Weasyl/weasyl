from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPServiceUnavailable
from pyramid.response import Response
from oauthlib.oauth2 import FatalClientError, OAuth2Error

from libweasyl.oauth import get_consumers_for_user, revoke_consumers_for_user, server
from weasyl.controllers.decorators import disallow_api, token_checked
from weasyl import define as d
from weasyl import media, orm
from weasyl.controllers.decorators import login_required


class OAuthResponse(Response):
    def __init__(self, headers, body, status):
        super(OAuthResponse, self).__init__(
            body=body,
            status_code=status,
            headers=headers,
        )


def extract_params(request):
    return request.path, request.method, request.params, request.headers


def render_form(request, scopes, credentials):
    db = d.connect()
    client = db.query(orm.OAuthConsumer).get(credentials['client_id'])
    user = db.query(orm.Login).get(request.userid)
    user_media = media.get_user_media(request.userid)
    credentials['scopes'] = scopes
    return d.render('oauth2/authorize.html', [
        scopes, credentials, client, user, user_media,
    ])


@disallow_api
def authorize_get_(request):
    if not request.userid:
        return Response(d.webpage(request.userid, "etc/signin.html", [
            False,
            request.path_qs,
        ], title="Sign In"))

    try:
        scopes, credentials = server.validate_authorization_request(*extract_params(request))
    except FatalClientError:
        raise HTTPBadRequest()
    except OAuth2Error as e:
        return HTTPFound(location=e.in_uri(e.redirect_uri))
    del credentials['request']
    return Response(render_form(request, scopes, credentials))


@disallow_api
@token_checked
@login_required
def authorize_post_(request):
    return HTTPServiceUnavailable()


@disallow_api
def token_(request):
    return HTTPServiceUnavailable()


def get_userid_from_authorization(request, scopes=['wholesite']):
    valid, oauth_request = server.verify_request(*(extract_params(request) + (scopes,)))
    if not valid:
        return None
    # TODO(hyena): I'm not sure where this property comes from. Find out.
    return oauth_request.userid


__all__ = [
    'get_consumers_for_user', 'revoke_consumers_for_user', 'get_userid_from_authorization',
]

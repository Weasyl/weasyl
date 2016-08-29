import anyjson as json
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.response import Response
from oauthlib.oauth2 import FatalClientError, OAuth2Error

from libweasyl.oauth import get_consumers_for_user, revoke_consumers_for_user, server
from weasyl.controllers.decorators import disallow_api, token_checked
from weasyl import define as d
from weasyl import errorcode, http, login, media, orm


def extract_params(request):
    headers = http.get_headers(request.environ)
    return request.path, request.method, request.params, headers


def render_form(request, scopes, credentials, mobile, error=None,
                username='', password='', remember_me=False, not_me=False):
    db = d.connect()
    client = db.query(orm.OAuthConsumer).get(credentials['client_id'])
    if request.userid:
        user = db.query(orm.Login).get(request.userid)
        user_media = media.get_user_media(request.userid)
    else:
        user = user_media = None
    credentials['scopes'] = scopes
    return d.render('oauth2/authorize.html', [
        scopes, credentials, client, user, user_media, mobile, error,
        username, password, remember_me, not_me,
    ])


@disallow_api
def authorize_get_(request):
    form = request.web_input(mobile='')
    try:
        scopes, credentials = server.validate_authorization_request(*extract_params(request))
    except FatalClientError:
        raise HTTPBadRequest()
    except OAuth2Error as e:
        return HTTPFound(location=e.in_uri(e.redirect_uri))
    del credentials['request']
    return Response(render_form(request, scopes, credentials, bool(form.mobile)))


@disallow_api
@token_checked
def authorize_post_(request):
    form = request.web_input(credentials='', username='', password='', remember_me='', mobile='', not_me='')
    try:
        credentials = json.loads(form.credentials)
    except ValueError:
        raise HTTPBadRequest()
    scopes = credentials.pop('scopes')
    error = None
    if form.not_me and form.username:
        userid, error = login.authenticate_bcrypt(form.username, form.password, bool(form.remember_me))
        if error:
            error = errorcode.login_errors.get(error, 'Unknown error.')
    elif not request.userid:
        error = "You must specify a username and password."
    else:
        userid = request.userid
    if error:
        return Response(render_form(request, scopes, credentials, bool(form.mobile), error,
                                    form.username, form.password, bool(form.remember_me),
                                    bool(form.not_me)))
    credentials['userid'] = userid
    headers, body, status = server.create_authorization_response(
        *(extract_params(request) + (scopes, credentials)))
    for k, v in headers.iteritems():
        request.set_header_on_response(k, v)
    request.set_status_on_response("%s Status" % (status,))
    return Response(body)


@disallow_api
def token_(request):
    headers, body, status = server.create_token_response(*extract_params())
    for k, v in headers.iteritems():
        request.set_header_on_response(k, v)
    request.set_status_on_response("%s Status" % (status,))
    return Response(body)


def get_userid_from_authorization(request, scopes=['wholesite']):
    valid, oauth_request = server.verify_request(*(extract_params(request) + (scopes,)))
    if not valid:
        return None
    # TODO(hyena): I'm not sure where this property comes from. Find out.
    return oauth_request.userid


__all__ = [
    'get_consumers_for_user', 'revoke_consumers_for_user',
]

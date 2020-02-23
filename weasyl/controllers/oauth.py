from __future__ import absolute_import

import json
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.view import view_config
from oauthlib.oauth2 import FatalClientError, OAuth2Error

from libweasyl.oauth import server

from weasyl import define as d
from weasyl import errorcode, login, media, orm, oauth2
from weasyl.controllers.decorators import disallow_api, token_checked


class OAuthResponse(Response):
    def __init__(self, headers, body, status):
        super(OAuthResponse, self).__init__(
            body=body,
            status_code=status,
            headers={k.encode('utf-8'): v.encode('utf-8') for k, v in headers.iteritems()},
        )


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
    return {
        'scopes': scopes,
        'credentials': credentials,
        'client': client,
        'myself': user,
        'my_media': user_media,
        'mobile': mobile,
        'error': error,
        'username': username,
        'password': password,
        'remember_me': remember_me,
        'not_me': not_me}


@view_config(route_name="oauth2_authorize", renderer='/oauth2/authorize.jinja2', request_method='GET')
@disallow_api
def authorize_get_(request):
    form = request.web_input(mobile='')
    try:
        scopes, credentials = server.validate_authorization_request(*oauth2.extract_params(request))
    except FatalClientError:
        raise HTTPBadRequest()
    except OAuth2Error as e:
        return HTTPFound(location=e.in_uri(e.redirect_uri))
    del credentials['request']
    return render_form(request, scopes, credentials, bool(form.mobile))


@view_config(route_name="oauth2_authorize", renderer='/oauth2/authorize.jinja2', request_method='POST')
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
        userid, error = login.authenticate_bcrypt(form.username, form.password, request=request if form.remember_me else None)
        if error:
            error = errorcode.login_errors.get(error, 'Unknown error.')
    elif not request.userid:
        error = "You must specify a username and password."
    else:
        userid = request.userid
    if error:
        return render_form(request, scopes, credentials, bool(form.mobile), error,
                           form.username, form.password, bool(form.remember_me),
                           bool(form.not_me))
    credentials['userid'] = userid
    response_attrs = server.create_authorization_response(
        *(oauth2.extract_params(request) + (scopes, credentials)))
    return OAuthResponse(*response_attrs)


@view_config(route_name="oauth2_token", request_method='POST')
@disallow_api
def token_(request):
    response_attrs = server.create_token_response(*oauth2.extract_params(request))
    return OAuthResponse(*response_attrs)

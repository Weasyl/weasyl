import anyjson as json
from oauthlib.oauth2 import FatalClientError, OAuth2Error
import web

from libweasyl.oauth import get_consumers_for_user, revoke_consumers_for_user, server
from libweasyl import staff, security
from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import define as d
from weasyl import errorcode, login, media, orm

_SCOPES = [
    {
        'name': 'wholesite',
        'description': 'FULL CONTROL - Note that this means the application can '
                       'perform almost any action as if you were logged in!',
    },
    {
        'name': 'identity',
        'description': 'Permission to retrieve your weasyl username and account number',
    },
    {
        'name': 'notifications',
        'description': 'Access to view your submission inbox, as well as notification counts '
                       'for comments, favs, messages, etc.',
    },
    {
        'name': 'favorite',
        'description': 'The ability to favorite and unfavorite submissions',
    },
]


def extract_params():
    headers = {k[5:].replace('_', '-').title(): v for k, v in web.ctx.env.iteritems() if k.startswith('HTTP_')}
    return web.ctx.path, web.ctx.method, web.input(), headers


class authorize_(controller_base):
    disallow_api = True

    def render_form(self, scopes, credentials, mobile, error=None,
                    username='', password='', remember_me=False, not_me=False):
        db = d.connect()
        client = db.query(orm.OAuthConsumer).get(credentials['client_id'])
        if self.user_id:
            user = db.query(orm.Login).get(self.user_id)
            user_media = media.get_user_media(self.user_id)
        else:
            user = user_media = None
        credentials['scopes'] = scopes
        detail_scopes = [scope for scope in _SCOPES if scope['name'] in scopes]
        return d.render('oauth2/authorize.html', [
            detail_scopes, credentials, client, user, user_media, mobile, error,
            username, password, remember_me, not_me,
        ])

    def GET(self):
        form = web.input(mobile='')
        try:
            scopes, credentials = server.validate_authorization_request(*extract_params())
        except FatalClientError:
            raise web.badrequest()
        except OAuth2Error as e:
            return web.found(e.in_uri(e.redirect_uri))
        del credentials['request']
        return self.render_form(scopes, credentials, bool(form.mobile))

    @d.token_checked
    def POST(self):
        form = web.input(credentials='', username='', password='', remember_me='', mobile='', not_me='')
        try:
            credentials = json.loads(form.credentials)
        except ValueError:
            raise web.badrequest()
        scopes = credentials.pop('scopes')
        error = None
        if form.not_me and form.username:
            userid, error = login.authenticate_bcrypt(form.username, form.password, bool(form.remember_me))
            if error:
                error = errorcode.login_errors.get(error, 'Unknown error.')
        elif not self.user_id:
            error = "You must specify a username and password."
        else:
            userid = self.user_id
        if error:
            return self.render_form(scopes, credentials, bool(form.mobile), error,
                                    form.username, form.password, bool(form.remember_me), bool(form.not_me))
        credentials['userid'] = userid
        headers, body, status = server.create_authorization_response(
            *(extract_params() + (scopes, credentials)))
        for k, v in headers.iteritems():
            web.header(k, v)
        web.ctx.status = '%s Status' % (status,)
        return body


class token_(controller_base):
    disallow_api = True

    def POST(self):
        headers, body, status = server.create_token_response(*extract_params())
        for k, v in headers.iteritems():
            web.header(k, v)
        web.ctx.status = '%s Status' % (status,)
        return body


def get_userid_from_authorization(scopes):
    """
    Attempt to validate an HTTP_Authorization request using OAuth2 workflow.
    This method automagically extracts information it requires from HTTP
    headers on the current request.

    :param scopes: The set of scopes that are required for an authorization
                   grant to be considered successful. scopes may be an empty
                   list, meaning OAuth2 applications with any configuration
                   of permissions should be allowed to access the requested resource.
    :return: a valid userid if the request could be verified, else NONE
    """
    valid, request = server.verify_request(*(extract_params() + (scopes,)))
    if not valid:
        return None
    return request.userid


__all__ = [
    'get_consumers_for_user', 'revoke_consumers_for_user',
]


def get_allowed_scopes(userid):
    """
    Get a list of oauth scopes this user is allowed to request
    :param userid: the userid of the application owner
    :return: a list of scopes
    """
    allowed = _SCOPES
    # only trusted individuals should be allowed to use the "wholesite" oauth grant
    if userid not in staff.ADMINS | staff.MODS | staff.DEVELOPERS:
        allowed = [scope for scope in allowed if scope['name'] != 'wholesite']
    return allowed


def register_client(userid, name, scopes, redirects, homepage):
    """
    Register an application as an OAuth2 consumer
    :param userid: the user registering this application
    :param name: the name of the application
    :param scopes: a list of the scopes registered for this application
    :param redirects: allowed redirect URIs for this application
    """
    if not name.strip():
        raise WeasylError("applicationNameMissing")
    if not scopes:
        raise WeasylError("applicationHasNoScope")

    session = d.connect()
    new_consumer = orm.OAuthConsumer(
        clientid=security.generate_key(32),
        description=name,
        ownerid=userid,
        grant_type="authorization_code",
        response_type="code",
        scopes=scopes,
        redirect_uris=redirects,
        client_secret=security.generate_key(64),
        homepage=homepage,
    )
    # this doesnt seem right
    session.begin()
    session.add(new_consumer)
    session.commit()


def get_registered_applications(userid):
    """
    Return a list of all OAuth2 consumers registered to this account
    """
    q = (orm.OAuthConsumer.query
         .filter_by(ownerid=userid))
    return q.all()


def remove_clients(userid, clients):
    """
    Delete a set of OAuth2 applications associated with a user.
    :param userid: the user making the request
    :param clients: a list of client ID's owned by this user to be removed
    """
    q = (orm.OAuthConsumer.query
         .filter_by(ownerid=userid)
         .filter(orm.OAuthConsumer.clientid.in_(clients)))
    q.delete(synchronize_session=False)


def renew_client_secrets(userid, clients):
    """
    Iterates over client IDs of OAuth2 applications
    and assigns each one a new client secret.
    To be used in the event of an oopsie.
    :param userid: the user making the request
    :param clients: a list of client ID's owned by this user to be renewed
    """
    for cid in clients:
        q = (orm.OAuthConsumer.query
             .filter_by(ownerid=userid)
             .filter_by(clientid=cid))
        q.update({orm.OAuthConsumer.client_secret: security.generate_key(64)},
                 synchronize_session=False)

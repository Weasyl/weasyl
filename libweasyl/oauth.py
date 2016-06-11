import arrow
from oauthlib.oauth2 import RequestValidator, WebApplicationServer

from libweasyl import cache
from libweasyl import security
from libweasyl import staff
from libweasyl.models.api import OAuthBearerToken, OAuthConsumer

SCOPES = {
    'wholesite': 'FULL CONTROL - Note that this means the application can '
                 'perform almost any action as if you were logged in!',
    'identity': 'Permission to retrieve your weasyl username and account number',
    'notifications': 'Access to view your submission inbox, as well as notification counts '
                     'for comments, favs, messages, etc.',
    'favorite': 'The ability to favorite and unfavorite submissions',
}

_SECRET_LENGTH = 64


class WeasylValidator(RequestValidator):
    def _get_client(self, client_id):
        return OAuthConsumer.query.get(client_id)

    def validate_client_id(self, client_id, request, *a, **kw):
        return self._get_client(client_id) is not None

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        client = self._get_client(client_id)
        return bool(client) and redirect_uri in client.redirect_uris

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return self._get_client(client_id).redirect_uris[0]

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        client_obj = self._get_client(client_id)
        if not client_obj:
            return False
        scopes = set(scopes)
        return (scopes & set(client_obj.scopes)) == scopes

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        client_obj = self._get_client(client_id)
        if not client_obj:
            return []
        return client_obj.scopes

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        client_obj = self._get_client(client_id)
        if not client_obj:
            return False
        return client_obj.response_type == response_type

    @classmethod
    def cache_key(cls, code):
        return 'oauth2-grant-tokens:%s' % (code,)

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        cache.region.set(
            self.cache_key(code['code']), {
                'client_id': request.client_id,
                'scopes': request.scopes,
                'redirect_uri': request.redirect_uri,
                'userid': request.userid})

    def authenticate_client(self, request, *args, **kwargs):
        if not request.client_id:
            return False
        client_obj = self._get_client(request.client_id)
        if not client_obj:
            return False
        elif 'client_secret' not in request.body:
            return False
        elif client_obj.client_secret != request.body['client_secret']:
            return False
        request.client = client_obj
        return True

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        return False

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        grant = cache.region.get(self.cache_key(code), expiration_time=60 * 10)
        if not grant:
            return False
        if grant['client_id'] != client_id:
            return False
        request.state = kwargs.get('state')
        request.userid = grant['userid']
        request.scopes = grant['scopes']
        return True

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        grant = cache.region.get(self.cache_key(code), expiration_time=60 * 10)
        return grant and grant['redirect_uri'] == redirect_uri

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        return grant_type in {'authorization_code', 'refresh_token'}

    def save_bearer_token(self, token, request, *args, **kwargs):
        db = OAuthBearerToken.dbsession
        if 'refresh_token' in request.body:
            bearer_token = self._get_bearer(refresh_token=request.body['refresh_token'])
        else:
            bearer_token = OAuthBearerToken(
                clientid=request.client_id,
                userid=request.userid,
                scopes=request.scopes,
            )
            db.add(bearer_token)
        bearer_token.access_token = token['access_token']
        bearer_token.refresh_token = token['refresh_token']
        bearer_token.expires_at = arrow.utcnow().replace(seconds=token['expires_in'])
        db.flush()

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        cache.region.delete(self.cache_key(code))

    def _get_bearer(self, **kw):
        q = OAuthBearerToken.query.filter_by(**kw)
        if 'access_token' in kw:
            q = q.filter(OAuthBearerToken.expires_at > arrow.utcnow())
        return q.first()

    def validate_bearer_token(self, token, scopes, request):
        bearer = self._get_bearer(access_token=token)
        if not bearer:
            return False
        scopes = set(scopes)
        bearer_scopes = set(bearer.scopes)
        # bearer only valid if it satisfied all scopes requested
        # wholesite permission implicitly grants all others
        if 'wholesite' not in bearer_scopes and (scopes & bearer_scopes) != scopes:
            return False
        request.userid = bearer.userid
        return True

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        bearer = self._get_bearer(refresh_token=refresh_token)
        if not bearer:
            return False
        request.userid = bearer.userid
        return True

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        bearer = self._get_bearer(refresh_token=refresh_token)
        if not bearer:
            return []
        return bearer.scopes


validator = WeasylValidator()
server = WebApplicationServer(validator)


def get_consumers_for_user(userid):
    q = (
        OAuthConsumer.query
        .join(OAuthBearerToken)
        .distinct(OAuthConsumer.clientid)
        .filter_by(userid=userid)
        .filter(OAuthBearerToken.expires_at > arrow.utcnow()))
    return q.all()


def revoke_consumers_for_user(userid, clientids):
    if not clientids:
        return
    q = (
        OAuthBearerToken.query
        .filter_by(userid=userid)
        .filter(OAuthBearerToken.clientid.in_(clientids)))
    q.delete('fetch')


def register_client(userid, name, scopes, redirects, homepage):
    """
    Register an application as an OAuth2 consumer
    :param userid: the user registering this application
    :param name: the name of the application
    :param scopes: a list of the scopes registered for this application
    :param redirects: allowed redirect URIs for this application
    :param homepage: The url of the project this consumer is for (optional)
    """

    allowed_scopes = set(get_allowed_scopes(userid).keys())
    scopes = set(scopes) & allowed_scopes
    if not scopes:
        raise ValueError("Must contain at least one scope")

    session = OAuthConsumer.dbsession
    clientid = "{}_{}".format(userid, security.generate_key(16))
    new_consumer = OAuthConsumer(
        clientid=clientid,
        description=name,
        ownerid=userid,
        grant_type="authorization_code",
        response_type="code",
        scopes=scopes,
        redirect_uris=redirects,
        client_secret=security.generate_key(_SECRET_LENGTH),
        homepage=homepage,
    )
    session.add(new_consumer)
    session.flush()


def get_registered_applications(userid):
    """
    Return a list of all OAuth2 consumers registered to this account
    """
    q = (OAuthConsumer.query
         .filter_by(ownerid=userid))
    return q.all()


def remove_clients(userid, clients):
    """
    Delete a set of OAuth2 applications associated with a user.
    :param userid: the user making the request
    :param clients: a list of client ID's owned by this user to be removed
    """
    q = (OAuthConsumer.query
         .filter_by(ownerid=userid)
         .filter(OAuthConsumer.clientid.in_(clients)))
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
        q = (OAuthConsumer.query
             .filter_by(ownerid=userid)
             .filter_by(clientid=cid))
        q.update({OAuthConsumer.client_secret: security.generate_key(64)},
                 synchronize_session=False)


def get_allowed_scopes(userid):
    """
    Get a list of oauth scopes this user is allowed to request
    :param userid: the userid of the application owner
    :return: a list of scopes
    """
    allowed = SCOPES.copy()
    # only trusted individuals should be allowed to use the "wholesite" oauth grant
    if userid not in staff.MODS | staff.DEVELOPERS:
        allowed.pop('wholesite', None)
    return allowed

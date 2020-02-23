from __future__ import absolute_import

from libweasyl.oauth import get_consumers_for_user, revoke_consumers_for_user, server


def extract_params(request):
    return request.path, request.method, request.params, request.headers


def get_userid_from_authorization(request, scopes=['wholesite']):
    valid, oauth_request = server.verify_request(*(extract_params(request) + (scopes,)))
    if not valid:
        return None
    # TODO(hyena): I'm not sure where this property comes from. Find out.
    return oauth_request.userid


__all__ = [
    'get_consumers_for_user', 'revoke_consumers_for_user',
]

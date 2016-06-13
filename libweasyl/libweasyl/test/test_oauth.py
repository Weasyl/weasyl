from libweasyl.test import common

import pytest

from libweasyl import oauth


def test_oauth_register_app(db):
    user = common.make_user(db)
    appname = "testclient"
    oauth.register_client(user.userid, appname, ['identity'], ['http://example.com'], '')
    oauth.register_client(user.userid, appname, ['favorite'], ['http://example.com'], '')
    registered = oauth.get_registered_applications(user.userid)
    assert len(registered) == 2
    assert registered[0].description == appname


@pytest.mark.parametrize(('in_scopes', 'out_scopes'), [
    (['identity'], ['identity']),
    (['identity', 'identity'], ['identity']),
    (['identity', 'fake_scope'], ['identity']),
    (['wholesite', 'favorite'], ['favorite']),
])
def test_oauth_invalid_scopes(db, in_scopes, out_scopes):
    """
    test that invalid scopes are not persisted to the database
    for the purpose of this test wholesite is an invalid scope
    because the generated user should not be in the list of staff.
    """
    user = common.make_user(db)
    oauth.register_client(user.userid, "test", in_scopes, ['http://example.com'], '')
    app = oauth.get_registered_applications(user.userid)[0]
    assert app.scopes == out_scopes


def test_oauth_register_consumer(db):
    """
    test that we can generate and retrieve an auth token
    """
    appowner = common.make_user(db)
    appuser = common.make_user(db)
    redirect = 'https://example.com'
    oauth.register_client(appowner.userid, "test", ['identity'], [redirect], '')
    app = oauth.get_registered_applications(appowner.userid)[0]
    headers, body, response_code = oauth.server.create_authorization_response(
        'https://weasyl.com/api/oauth/authorize',
        'POST',
        {
            'response_type': 'code',
            'client_id': app.clientid,
            'redirect_uri': redirect,
            'state': 'clientstate',
        },
        None,
        ['identity'],
        {"userid": appuser.userid},
    )
    loc = headers['Location']
    # if code stops being the last parameter passed back then i'm sorry
    code = loc[loc.find("code=")+5:]
    oauth.server.create_token_response(
        'https://weasyl.com/api/oauth/token',
        'POST',
        {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": app.clientid,
            "client_secret": app.client_secret,
            "redirect_uri": redirect
        },
        None,
        {"userid": appuser.userid},
    )
    consumers = oauth.get_consumers_for_user(appuser.userid)
    assert len(consumers) == 1
    assert consumers[0].owner.profile.userid == appowner.userid

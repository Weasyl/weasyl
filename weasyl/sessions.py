import secrets
from libweasyl.models.users import Session


_USER_TOKEN_BYTES = 16


def create_session(userid):
    return Session(
        userid=userid,
        sessionid=secrets.token_urlsafe(_USER_TOKEN_BYTES),
    )

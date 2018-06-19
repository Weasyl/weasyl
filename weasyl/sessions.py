from libweasyl import security
from libweasyl.models.users import GuestSession, Session


USER_TOKEN_LENGTH = 64
GUEST_TOKEN_LENGTH = 20


def create_session(userid):
    sess = Session(userid=userid)
    sess.sessionid = security.generate_key(USER_TOKEN_LENGTH)
    sess.create = True
    sess.save = True
    return sess


def create_guest_session():
    token = security.generate_key(GUEST_TOKEN_LENGTH)
    sess = GuestSession(token)
    sess.create = True
    return sess


def is_guest_token(token):
    token = str(token)
    return len(token) == GUEST_TOKEN_LENGTH and token.isalnum()

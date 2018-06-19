from libweasyl import security
from libweasyl.models.users import Session


def create_session(userid):
    sess_obj = Session(userid=userid)
    sess_obj.sessionid = security.generate_key(64)
    sess_obj.create = True
    sess_obj.save = True
    return sess_obj

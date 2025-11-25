from sqlalchemy import orm

from libweasyl.models.meta import Base
from libweasyl.models import tables


class Login(Base):
    """
    A Weasyl user account, which can be used to log into the site.
    """

    __table__ = tables.login


class Profile(Base):
    """
    A user's profile information.
    """

    __table__ = tables.profile

    user = orm.relationship(Login, backref=orm.backref('profile', uselist=False, lazy='joined'))


class Session(Base):
    """
    A Weasyl login session.
    """

    __table__ = tables.sessions

    user = orm.relationship(Login)

    def __repr__(self):
        return '<Session for %s: %r>' % (self.userid, self.additional_data)


class Friendship(Base):
    __table__ = tables.frienduser

import datetime

import arrow
from dateutil.relativedelta import relativedelta
import pytz
from pyramid.decorator import reify
from sqlalchemy import orm

from libweasyl.models.helpers import clauses_for
from libweasyl.models.meta import Base
from libweasyl.models import tables
from libweasyl import cache


class Login(Base):
    """
    A Weasyl user account, which can be used to log into the site.
    """

    __table__ = tables.login

    @reify
    def media(self):
        from libweasyl.media import get_user_media
        return get_user_media(self.userid)

    @reify
    def avatar_display_url(self):
        avatar = self.media.get('avatar')
        return avatar and avatar[0]['display_url']


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
    save = False
    create = False

    user = orm.relationship(Login, backref='sessions')

    def __repr__(self):
        return '<Session for %s: %r>' % (self.userid, self.additional_data)

    @reify
    def timezone(self):
        if not self.userid:
            return _server_time
        else:
            return UserTimezone.load_from_memcached_or_database(self.userid) or _server_time


class GuestSession(object):
    __slots__ = ('sessionid', 'csrf_token', 'create')

    userid = None
    additional_data = None

    def __init__(self, sessionid):
        self.sessionid = sessionid
        self.csrf_token = sessionid
        self.create = False


class UserTimezone(Base):
    """
    A user's timezone information.
    """

    __table__ = tables.user_timezones

    def __repr__(self):
        return '<UserTimezone %#x: user %s; tz %r>' % (
            id(self), self.userid, self.timezone)

    def localtime(self, dt):
        tz = pytz.timezone(self.timezone)
        return tz.normalize(dt.astimezone(tz))

    def localtime_from_timestamp(self, target):
        dt = datetime.datetime.utcfromtimestamp(target).replace(tzinfo=pytz.utc)
        return self.localtime(dt)

    @classmethod
    def cache_key(cls, userid):
        return 'user-timezone:%d' % (userid,)

    def cache(self):
        cache.region.set(self.cache_key(self.userid), self.timezone)

    @classmethod
    def load_from_memcached_or_database(cls, userid):
        tz = cache.region.get(cls.cache_key(userid))
        if tz:
            return cls(userid=userid, timezone=tz)
        inst = cls.query.get(userid)
        if inst is not None:
            inst.cache()
        return inst


class UserInfo(Base):
    """
    A user's personal information.
    """

    __table__ = tables.userinfo

    user = orm.relationship(Login, backref=orm.backref('info', uselist=False))

    @property
    def age(self):
        return relativedelta(arrow.get().datetime, self.birthday.datetime).years


class Friendship(Base):
    __table__ = tables.frienduser

    with clauses_for(__table__) as c:
        is_pending = c('pending')


class Ignorama(Base):
    __table__ = tables.ignoreuser


class Follow(Base):
    __table__ = tables.watchuser


_server_time = GuestSession.timezone = UserTimezone(timezone='America/Denver')

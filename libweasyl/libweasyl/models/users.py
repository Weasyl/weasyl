import datetime
import logging

import arrow
import bcrypt
from dateutil.relativedelta import relativedelta
import pytz
from pyramid.decorator import reify
from sqlalchemy import orm
import sqlalchemy as sa

from libweasyl.common import minimize_media
from libweasyl.models.helpers import clauses_for
from libweasyl.models.meta import Base
from libweasyl.models import tables
from libweasyl import cache, ratings, staff


log = logging.getLogger(__name__)


_BLANK_AVATAR = "/static/images/avatar_default.jpg"


class Login(Base):
    """
    A Weasyl user account, which can be used to log into the site.
    """

    __table__ = tables.login

    default_avatar = {
        'display_url': _BLANK_AVATAR,
        'file_url': _BLANK_AVATAR,
    }

    def _comment_criteria(self):
        return {'target_user': self.userid}

    def canonical_path(self, request, operation=None):
        """
        Returns the canonical URL for this user's profile.
        """
        parts = ['~' + self.login_name]
        if operation is not None:
            parts.append(operation)
        return request.resource_path(None, *parts)

    @reify
    def media(self):
        from libweasyl.media import get_user_media
        return get_user_media(self.userid)

    @reify
    def avatar(self):
        if 'avatar' in self.media:
            return self.media['avatar'][0]
        else:
            return self.default_avatar

    @reify
    def banner(self):
        if not self.media.get('banner'):
            return None
        return self.media['banner'][0]

    @reify
    def is_staff(self):
        return self.userid in staff.MODS

    def is_friends_with(self, other):
        """
        Returns True if this user is in a friendship with the other user, or
        False otherwise.
        """
        return bool(
            Friendship.query
            .filter(sa.or_(
                (Friendship.userid == self.userid) & (Friendship.otherid == other),
                (Friendship.otherid == self.userid) & (Friendship.userid == other)))
            .count())

    def is_ignoring(self, other):
        """
        Returns True if this user is ignoring the other user, or False
        otherwise.
        """
        return bool(
            Ignorama.query
            .filter(
                (Ignorama.userid == self.userid) & (Ignorama.otherid == other))
            .count())

    def is_ignored_by(self, other):
        """
        Returns True if the other user is ignoring this user, or False
        otherwise.
        """
        return bool(
            Ignorama.query
            .filter(
                (Ignorama.userid == other) & (Ignorama.otherid == self.userid))
            .count())

    def is_permitted_rating(self, rating):
        """
        Returns True if this user's is old enough to view content with the
        given rating. Otherwise, returns False.
        """
        return self.info.age >= rating.minimum_age

    def can_view_rating(self, rating):
        """
        Return True if this user is permitted to and has opted to view content
        with the given rating. Otherwise, returns False.
        """
        if not self.is_permitted_rating(rating):
            return False
        return self.profile.maximum_content_rating >= rating

    def __json__(self, request):
        """
        Returns a dictionary representing this user for export to JSON.
        """
        return {
            'login': self.login_name,
            'username': self.profile.username,
            'full_name': self.profile.full_name,
            'media': minimize_media(request, getattr(self, 'media', None)),
        }


class AuthBCrypt(Base):
    """
    A user's bcrypt-hashed password.
    """

    __table__ = tables.authbcrypt

    user = orm.relationship(Login, backref=orm.backref('bcrypt', uselist=False))

    def set_password(self, password):
        """
        Sets the user's password to the new password provided.
        """
        self.hashsum = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(13))


class Profile(Base):
    """
    A user's profile information.
    """

    __table__ = tables.profile

    user = orm.relationship(Login, backref=orm.backref('profile', uselist=False, lazy='joined'))

    _tagging_level_to_rating = {
        'max-rating-explicit': ratings.EXPLICIT,
        'max-rating-mature': ratings.MATURE,
        None: ratings.GENERAL,
    }

    @property
    def maximum_content_rating(self):
        return self._tagging_level_to_rating[self.config['tagging-level']]


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


class UserStream(Base):
    """
    Stream information.
    """
    __table__ = tables.user_streams

    owner = orm.relationship(Login, backref='user_streams')


class Friendship(Base):
    __table__ = tables.frienduser

    with clauses_for(__table__) as c:
        is_pending = c('pending')


class Ignorama(Base):
    __table__ = tables.ignoreuser


class Follow(Base):
    __table__ = tables.watchuser


_server_time = GuestSession.timezone = UserTimezone(timezone='America/Denver')

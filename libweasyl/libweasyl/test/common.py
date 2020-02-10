import datetime
import itertools

import arrow
from dateutil.relativedelta import relativedelta
import py.path

from libweasyl.models import content, users
from libweasyl import media, ratings


datadir = py.path.local(__file__).dirpath('data')
_user_counter = itertools.count()


class NotFound(Exception):
    """
    A fake 'not found' exception to be raised in place of a web framework's
    'not found' exception.
    """


def dummy_format_media_link(media, link):
    return None


def user_with_age(age):
    """
    Create a Login, UserInfo, and Profile with the provided age.

    Note that the new model objects are not added to the session.

    Returns:
        Login: The user Login object created.
    """
    birthday = arrow.get(datetime.datetime.utcnow() - relativedelta(years=age))
    login_name = 'user%d' % next(_user_counter)
    return users.Login(
        info=users.UserInfo(birthday=birthday),
        profile=users.Profile(username=login_name, full_name=login_name, unixtime=arrow.get(0)),
        last_login=arrow.get(0),
        login_name=login_name)


def media_item(db, filename, file_type=None):
    """
    Create a media item from the given data file name.

    The media item created is added to the session.

    Returns:
        A MediaItem.
    """
    if file_type is None:
        _, _, file_type = filename.rpartition('.')
    data = datadir.join(filename).read(mode='rb')
    item = media.MediaItem.fetch_or_create(data, file_type=file_type)
    db.flush()
    return item


def make_user(db):
    """
    Create a new user.

    The model objects created are added to the session.

    Returns:
        Login: The user Login object created.
    """
    user = user_with_age(42)
    db.add(user)
    db.flush()
    return user


def make_friendship(db, user1, user2):
    """
    Create a friendship between two users.

    The Friendship object created is added to the session.
    """
    db.add(users.Friendship(userid=user1.userid, otherid=user2.userid))
    db.flush()


def make_password(db, user, hashsum='$2a$13$pr8cpRxMMbiYfyuEnJ9Cl./QiO9yK7A/H/f9.CQ2DTGyIFgwDHCIa'):
    """
    Add a password to a user.

    The default password is 'password'. The AuthBCrypt object created is added
    to the session.
    """
    db.add(users.AuthBCrypt(user=user, hashsum=hashsum))
    db.flush()


def make_submission(db, settings=()):
    """
    Create a new submission.

    A new user is also created to be the owner of the submission. Both the user
    objects and the submission object are added to the session.

    Returns:
        Submission: The Submission object created.
    """
    owner = make_user(db)
    sub = content.Submission(
        owner=owner, title='', content='', subtype=1, rating=ratings.GENERAL,
        unixtime=arrow.get(0), sorttime=arrow.get(0), settings=None)
    if settings:
        sub.settings.mutable_settings.update(settings)
    db.add(sub)
    db.flush()
    return sub


def make_media(db):
    """
    Create a new media item.

    The file used for the media item is fixed: the data file '2x233.gif'.

    Returns:
        A MediaItem.
    """
    return media_item(db, '2x233.gif')

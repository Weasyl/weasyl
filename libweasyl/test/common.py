import itertools

import arrow
import py.path

from libweasyl.models import content, tables, users
from libweasyl import media, ratings


datadir = py.path.local(__file__).dirpath('data')
_user_counter = itertools.count()


def dummy_format_media_link(media, link):
    return None


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
    login_name = 'user%d' % next(_user_counter)
    user = users.Login(
        profile=users.Profile(username=login_name, full_name=login_name, created_at=arrow.get(0).datetime),
        last_login=arrow.get(0).datetime,
        login_name=login_name)
    db.add(user)
    db.flush()
    db.execute(tables.userinfo.insert(), {
        'userid': user.userid,
    })
    return user


def make_submission(db):
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
        unixtime=arrow.get(0), favorites=0)
    db.add(sub)
    db.flush()
    return sub

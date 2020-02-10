from __future__ import absolute_import

import itertools

import arrow

from libweasyl import ratings
from libweasyl import staff
from libweasyl.legacy import get_sysname
from libweasyl.models import content, users
from libweasyl.models.content import Journal
import weasyl.define as d
from weasyl import favorite
from weasyl import login
from weasyl import orm
from weasyl import sessions

_user_index = itertools.count()
TEST_DATABASE = "weasyl_test"


def add_entity(entity):
    db = d.connect()
    db.add(entity)
    db.flush()
    return entity


def update_last_submission_time(userid, unixtime):
    profile = d.meta.tables['profile']
    db = d.connect()
    db.execute(profile.update().where(profile.c.userid == userid).values(latest_submission_time=unixtime))
    db.flush()


def create_api_key(userid, token, description=""):
    add_entity(orm.APIToken(userid=userid, token=token, description=description))


def create_user(full_name="", birthday=arrow.get(586162800), config=None,
                username=None, password=None, email_addr=None, user_id=None,
                verified=True):
    """ Creates a new user and profile, and returns the user ID. """
    if username is None:
        username = "User-" + str(next(_user_index))

    while True:
        user = add_entity(users.Login(login_name=get_sysname(username),
                                      last_login=arrow.get(0)))

        if user.userid not in staff.MODS and user.userid not in staff.DEVELOPERS:
            break

        db = d.connect()
        db.delete(user)
        db.flush()

    add_entity(users.Profile(userid=user.userid, username=username,
                             full_name=full_name, unixtime=arrow.get(0), config=config))
    add_entity(users.UserInfo(userid=user.userid, birthday=birthday))
    # Verify this user
    if verified:
        d.engine.execute("UPDATE login SET voucher = userid WHERE userid = %(id)s",
                         id=user.userid)
    # Set a password for this user
    if password is not None:
        d.engine.execute("INSERT INTO authbcrypt VALUES (%(id)s, %(bcrypthash)s)",
                         id=user.userid, bcrypthash=login.passhash(password))
    # Set an email address for this user
    if email_addr is not None:
        d.engine.execute("UPDATE login SET email = %(email)s WHERE userid = %(id)s",
                         email=email_addr, id=user.userid)
    # Force the userID to a user-defined value and return it
    if user_id is not None:
        d.engine.execute("UPDATE login SET userid = %(newid)s WHERE userid = %(oldid)s", newid=user_id, oldid=user.userid)
        return user_id
    return user.userid


def create_session(user):
    """
    Creates a session for a user and returns the corresponding WZL cookie.
    """
    session = sessions.create_session(user)

    db = d.connect()
    db.add(session)
    db.flush()

    return 'WZL=' + session.sessionid.encode('utf-8')


def create_folder(userid, title="Folder", parentid=0, settings=None):
    folder = add_entity(content.Folder(userid=userid, title=title, parentid=parentid,
                                       settings=settings))
    return folder.folderid


def create_submission(userid, title="", rating=ratings.GENERAL.code, unixtime=arrow.get(1),
                      description="", folderid=None, subtype=0, settings=None):
    """ Creates a new submission, and returns its ID. """
    submission = add_entity(content.Submission(
        userid=userid, rating=rating, title=title, unixtime=unixtime, content=description,
        folderid=folderid, subtype=subtype, sorttime=arrow.get(0), settings=settings, favorites=0))
    update_last_submission_time(userid, unixtime)
    return submission.submitid


def create_submissions(count, userid, title="", rating=ratings.GENERAL.code,
                       unixtime=arrow.get(1), description="", folderid=None, subtype=0,
                       settings=None):
    """ Creates multiple submissions, and returns their IDs. """
    results = []
    for i in range(count):
        results.append(create_submission(userid, title, rating, unixtime, description,
                                         folderid, subtype, settings))
    return results


def create_submission_comment(userid, targetid, parentid=None, body="",
                              unixtime=arrow.get(1), settings=None):
    comment = add_entity(content.Comment(
        userid=userid, target_sub=targetid, parentid=parentid, content=body,
        unixtime=unixtime, settings=settings))
    return comment.commentid


def create_journal_comment(userid, targetid, parentid=None, body="",
                           unixtime=arrow.get(1), settings=None):
    comment = add_entity(content.JournalComment(
        userid=userid, targetid=targetid, parentid=parentid, content=body,
        unixtime=unixtime, settings=settings))
    return comment.commentid


def create_character_comment(userid, targetid, parentid=None, body="",
                             unixtime=arrow.get(1), settings=None):
    comment = add_entity(content.CharacterComment(
        userid=userid, targetid=targetid, parentid=parentid, content=body,
        unixtime=unixtime, settings=settings))
    return comment.commentid


def create_shout(userid, targetid, parentid=None, body="",
                 unixtime=arrow.get(1), settings=None):
    comment = add_entity(content.Comment(
        userid=userid, target_user=targetid, parentid=parentid, content=body,
        unixtime=unixtime, settings=settings))
    return comment.commentid


def create_journal(userid, title='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None, content=''):
    journal = add_entity(Journal(
        userid=userid, title=title, rating=rating, unixtime=unixtime, settings=settings, content=content))
    update_last_submission_time(userid, unixtime)
    return journal.journalid


def create_journals(count, userid, title='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None):
    results = []
    for i in range(count):
        results.append(create_journal(userid, title, rating, unixtime, settings))
    return results


def create_character(userid, name='', age='', gender='', height='', weight='', species='',
                     description='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None):
    character = add_entity(content.Character(
        userid=userid, char_name=name, age=age, gender=gender, height=height, weight=weight,
        species=species, content=description, rating=rating, unixtime=unixtime, settings=settings))
    update_last_submission_time(userid, unixtime)
    return character.charid


def create_characters(count, userid, name='', age='', gender='', height='', weight='', species='',
                      description='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None):
    results = []
    for i in range(count):
        results.append(create_character(
            userid, name, age, gender, height, weight, species, description,
            rating, unixtime, settings))
    return results


def create_friendship(user1, user2, settings=None):
    db = d.connect()
    db.add(users.Friendship(userid=user1, otherid=user2, settings=settings))
    db.flush()


def create_follow(user1, user2, settings='scftj'):
    db = d.connect()
    db.add(users.Follow(userid=user1, otherid=user2, settings=settings))
    db.flush()


def create_ignoreuser(ignorer, ignoree):
    db = d.connect()
    db.add(users.Ignorama(userid=ignorer, otherid=ignoree))
    db.flush()


# TODO: do these two in a less bad way
def create_banuser(userid, reason):
    query = d.engine.execute(
        "UPDATE login SET settings = REPLACE(REPLACE(settings, 'b', ''), 's', '') || 'b' WHERE userid = %(target)s",
        target=userid)

    assert query.rowcount == 1

    d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=userid)
    d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=userid)
    d.engine.execute("INSERT INTO permaban VALUES (%(target)s, %(reason)s)", target=userid, reason=reason)


def create_suspenduser(userid, reason, release):
    query = d.engine.execute(
        "UPDATE login SET settings = REPLACE(REPLACE(settings, 'b', ''), 's', '') || 's' WHERE userid = %(target)s",
        target=userid)

    assert query.rowcount == 1

    d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=userid)
    d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=userid)
    d.engine.execute("INSERT INTO suspension VALUES (%(target)s, %(reason)s, %(release)s)", target=userid, reason=reason, release=release)


def create_tag(title):
    tag = add_entity(content.Tag(title=title))
    return tag.tagid


def create_journal_tag(tagid, targetid, settings=None):
    db = d.connect()
    db.add(
        content.JournalTag(tagid=tagid, targetid=targetid, settings=settings))
    db.flush()


def create_character_tag(tagid, targetid, settings=None):
    db = d.connect()
    db.add(
        content.CharacterTag(tagid=tagid, targetid=targetid, settings=settings))
    db.flush()


def create_submission_tag(tagid, targetid, settings=None):
    db = d.connect()
    db.add(
        content.SubmissionTag(tagid=tagid, targetid=targetid, settings=settings))
    db.flush()

    db.execute(
        'INSERT INTO submission_tags (submitid, tags) VALUES (:submission, ARRAY[:tag]) '
        'ON CONFLICT (submitid) DO UPDATE SET tags = submission_tags.tags || :tag',
        {'submission': targetid, 'tag': tagid})


def create_blocktag(userid, tagid, rating):
    db = d.connect()
    db.add(content.Blocktag(userid=userid, tagid=tagid, rating=rating))
    db.flush()


def create_favorite(userid, **kwargs):
    unixtime = kwargs.pop('unixtime', None)
    favorite.insert(userid, **kwargs)

    if unixtime is not None:
        if 'submitid' in kwargs:
            type_ = 's'
        elif 'charid' in kwargs:
            type_ = 'c'
        elif 'journalid' in kwargs:
            type_ = 'j'

        targetid = d.get_targetid(*kwargs.values())

        fav = content.Favorite.query.filter_by(userid=userid, type=type_, targetid=targetid).one()
        fav.unixtime = unixtime
        content.Favorite.dbsession.flush()

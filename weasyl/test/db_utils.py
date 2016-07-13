import itertools

import arrow

from libweasyl.models import content, users
from libweasyl import legacy, ratings
import weasyl.define as d
from weasyl import login
from weasyl import orm

_user_index = itertools.count()
TEST_DATABASE = "weasyl_test"


def add_entity(entity):
    db = d.connect()
    db.add(entity)
    db.flush()
    return entity


def create_api_key(userid, token, description=""):
    add_entity(orm.APIToken(userid=userid, token=token, description=description))


def create_user(full_name="", birthday=arrow.get(586162800), config=None,
                username=None, password=None, email_addr=None, user_id=None):
    """ Creates a new user and profile, and returns the user ID. """
    if username is None:
        username = "User-" + str(next(_user_index))
    user = add_entity(users.Login(login_name=legacy.login_name(username),
                                  last_login=arrow.get(0)))
    add_entity(users.Profile(userid=user.userid, username=username,
                             full_name=full_name, unixtime=arrow.get(0), config=config))
    add_entity(users.UserInfo(userid=user.userid, birthday=birthday))
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


def create_folder(userid, title="Folder", parentid=0, settings=None):
    folder = add_entity(content.Folder(userid=userid, title=title, parentid=parentid,
                                       settings=settings))
    return folder.folderid


def create_submission(userid, title="", rating=ratings.GENERAL.code, unixtime=arrow.get(1),
                      description="", folderid=None, subtype=0, settings=None):
    """ Creates a new submission, and returns its ID. """
    submission = add_entity(content.Submission(
        userid=userid, rating=rating, title=title, unixtime=unixtime, content=description,
        folderid=folderid, subtype=subtype, sorttime=arrow.get(0), settings=settings))
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


def create_journal(userid, title='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None):
    journal = add_entity(content.Journal(
        userid=userid, title=title, rating=rating, unixtime=unixtime, settings=settings))
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


def create_favorite(userid, targetid, type, unixtime=arrow.get(1), settings=None):
    db = d.connect()
    db.add(content.Favorite(userid=userid, targetid=targetid, type=type,
                            unixtime=unixtime, settings=settings))
    db.flush()

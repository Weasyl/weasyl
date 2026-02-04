import datetime
import itertools

import arrow
import sqlalchemy as sa

from libweasyl import ratings
from libweasyl import staff
from libweasyl.models import content
from libweasyl.models.content import Journal
from libweasyl.models.helpers import CharSettings
import weasyl.define as d
from weasyl import favorite
from weasyl import login
from weasyl import orm
from weasyl import sessions
from weasyl.users import Username

_user_index = itertools.count()

_DEFAULT_PASSWORD = "$2b$04$IIdgY7gIpBckJI.YZQ3nHOo.Gh5j2lLhoTEPnWJplnfdpIOSoHYcu"


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


def create_user(
    full_name: str | None = None,
    *,
    birthday: datetime.date | None = None,
    username: str | None = None,
    password: str | None = None,
    email_addr: str = "",
    verified: bool = True,
    premium: bool = False,
    profile_guests: bool = True,
    max_rating: ratings.Rating = ratings.GENERAL,
) -> int:
    """ Creates a new user and profile, and returns the user ID. """
    if username is None:
        username = "User-" + str(next(_user_index))

    config = CharSettings(set(), {}, {})
    if premium:
        config.mutable_settings.add('premium')
    if not profile_guests:
        config.mutable_settings.add('hide-profile-from-guests')
    if max_rating != ratings.GENERAL:
        config['tagging-level'] = f'max-rating-{max_rating.name}'

    db = d.connect()

    with db.begin():
        # Find an unprivileged userid
        while True:
            userid = db.scalar("SELECT nextval('login_userid_seq')")
            if userid not in staff.MODS and userid not in staff.DEVELOPERS:
                break

        db.execute(d.meta.tables['login'].insert().values({
            'userid': userid,
            'login_name': Username.from_stored(username).sysname,
            'last_login': sa.text("to_timestamp(0)"),
            'email': email_addr,
            'voucher': userid if verified else None,
        }))

        db.execute(d.meta.tables['profile'].insert().values({
            **login.initial_profile(userid, username),
            'created_at': sa.text("to_timestamp(0)"),
            **({'full_name': full_name} if full_name is not None else {}),
            'config': config,
            'premium': premium,
        }))

        db.execute(d.meta.tables['userinfo'].insert(), {
            'userid': userid,
            'birthday': birthday,
        })

        # Set a password for this user
        db.execute(d.meta.tables['authbcrypt'].insert(), {
            'userid': userid,
            'hashsum': _DEFAULT_PASSWORD if password is None else login.passhash(password),
        })

    return userid


def create_session(user):
    """
    Creates a session for a user and returns the corresponding WZL cookie.
    """
    session = sessions.create_session(user)

    db = d.connect()
    db.add(session)
    db.flush()

    return 'WZL=' + session.sessionid


def create_folder(userid, title="Folder", parentid=0, settings=None):
    folder = add_entity(content.Folder(userid=userid, title=title, parentid=parentid,
                                       settings=settings))
    return folder.folderid


def create_submission(userid, title="Test title", rating=ratings.GENERAL.code, unixtime=arrow.get(1),
                      description="", folderid=None, subtype=0, hidden=False,
                      friends_only=False, critique=False
                      ):
    """ Creates a new submission, and returns its ID. """
    submission = add_entity(content.Submission(
        userid=userid, rating=rating, title=title, unixtime=unixtime, content=description,
        folderid=folderid, subtype=subtype, hidden=hidden,
        friends_only=friends_only, critique=critique,
        favorites=0))
    update_last_submission_time(userid, unixtime)
    return submission.submitid


def create_submissions(count, userid, title="", rating=ratings.GENERAL.code,
                       unixtime=arrow.get(1), description="", folderid=None, subtype=0,
                       hidden=False, friends_only=False, critique=False):
    """ Creates multiple submissions, and returns their IDs. """
    results = []
    for i in range(count):
        results.append(create_submission(userid, title, rating, unixtime, description,
                                         folderid, subtype, hidden, friends_only, critique))
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


def create_journal(userid, title='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), content='', *, hidden=False, friends_only=False) -> int:
    journal = add_entity(Journal(
        userid=userid, title=title, rating=rating, unixtime=unixtime, content=content,
        hidden=hidden, friends_only=friends_only))
    update_last_submission_time(userid, unixtime)
    return journal.journalid


def create_journals(count, userid, title='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), *, friends_only=False):
    results = []
    for i in range(count):
        results.append(create_journal(userid, title, rating, unixtime, friends_only=friends_only))
    return results


def create_character(userid, name='', age='', gender='', height='', weight='', species='',
                     description='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None, *, friends_only=False):
    character = add_entity(content.Character(
        userid=userid, char_name=name, age=age, gender=gender, height=height, weight=weight,
        species=species, content=description, rating=rating, unixtime=unixtime, settings=settings, friends_only=friends_only))
    update_last_submission_time(userid, unixtime)
    return character.charid


def create_characters(count, userid, name='', age='', gender='', height='', weight='', species='',
                      description='', rating=ratings.GENERAL.code, unixtime=arrow.get(1), settings=None, *, friends_only=False):
    results = []
    for i in range(count):
        results.append(create_character(
            userid, name, age, gender, height, weight, species, description,
            rating, unixtime, settings, friends_only=friends_only))
    return results


def create_friendship(user1: int, user2: int, pending: bool = False) -> None:
    db = d.connect()
    db.execute("INSERT INTO frienduser (userid, otherid, settings) VALUES (:userid, :otherid, :settings)", {
        "userid": user1,
        "otherid": user2,
        "settings": "p" if pending else "",
    })


def create_follow(user1: int, user2: int) -> None:
    db = d.connect()
    db.execute("INSERT INTO watchuser (userid, otherid, settings) VALUES (:userid, :otherid, 'scftj')", {
        "userid": user1,
        "otherid": user2,
    })


def create_ignoreuser(ignorer: int, ignoree: int) -> None:
    db = d.connect()
    db.execute("INSERT INTO ignoreuser (userid, otherid) VALUES (:userid, :otherid)", {
        "userid": ignorer,
        "otherid": ignoree,
    })


# TODO: do these two in a less bad way
def create_banuser(userid, reason):
    d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=userid)
    d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=userid)
    d.engine.execute("INSERT INTO permaban VALUES (%(target)s, %(reason)s)", target=userid, reason=reason)


def create_suspenduser(userid, reason, release):
    d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=userid)
    d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=userid)
    d.engine.execute("INSERT INTO suspension VALUES (%(target)s, %(reason)s, %(release)s)", target=userid, reason=reason, release=release)


def create_tag(title):
    return d.engine.scalar("INSERT INTO searchtag (title) VALUES (%(title)s) RETURNING tagid", title=title)


def create_journal_tag(tagid, targetid):
    d.engine.execute(
        'INSERT INTO searchmapjournal (tagid, targetid)'
        ' VALUES (%(tag)s, %(journal)s)',
        tag=tagid,
        journal=targetid,
    )


def create_character_tag(tagid, targetid):
    d.engine.execute(
        'INSERT INTO searchmapchar (tagid, targetid)'
        ' VALUES (%(tag)s, %(char)s)',
        tag=tagid,
        char=targetid,
    )


def create_submission_tag(tagid, targetid, settings=None):
    d.engine.execute(
        'INSERT INTO searchmapsubmit (tagid, targetid, settings)'
        ' VALUES (%(tag)s, %(sub)s, %(settings)s)',
        tag=tagid,
        sub=targetid,
        settings=settings or '',
    )

    d.engine.execute(
        'INSERT INTO submission_tags (submitid, tags)'
        ' VALUES (%(sub)s, ARRAY[%(tag)s])'
        ' ON CONFLICT (submitid) DO UPDATE SET tags = submission_tags.tags || %(tag)s',
        sub=targetid,
        tag=tagid,
    )


def create_blocktag(userid, tagid, rating):
    d.engine.execute(d.meta.tables['blocktag'].insert(), {
        'userid': userid,
        'tagid': tagid,
        'rating': rating,
    })


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

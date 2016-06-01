# journal.py

import arrow

from error import WeasylError
import macro as m
import define as d

import files
import comment
import profile
import welcome
import blocktag
import searchtag
import frienduser
import ignoreuser

import report
import favorite

from libweasyl import ratings
from libweasyl import text
from libweasyl import staff

from weasyl import media
from weasyl import orm


def create(userid, journal, friends_only=False, tags=None):
    # Check invalid arguments
    if not journal.title:
        raise WeasylError("titleInvalid")
    elif not journal.content:
        raise WeasylError("contentInvalid")
    elif not journal.rating:
        raise WeasylError("ratingInvalid")
    profile.check_user_rating_allowed(userid, journal.rating)

    # Assign settings
    settings = "f" if friends_only else ""

    # Create journal
    jo = d.meta.tables["journal"]

    journalid = d.engine.execute(jo.insert().returning(jo.c.journalid), {
        "userid": userid,
        "title": journal.title,
        "rating": journal.rating.code,
        "unixtime": arrow.now(),
        "settings": settings,
    }).scalar()

    # Write journal file
    files.make_path(journalid, "journal")
    files.write(files.make_resource(userid, journalid, "journal/submit"),
                journal.content)

    # Assign search tags
    searchtag.associate(userid, tags, journalid=journalid)

    # Create notifications
    if "m" not in settings:
        welcome.journal_insert(userid, journalid, rating=journal.rating.code,
                               settings=settings)

    d.metric('increment', 'journals')

    return journalid


def _select_journal_and_check(userid, journalid, rating=None, ignore=True, anyway=False, increment_views=True):
    """Selects a journal, after checking if the user is authorized, etc.

    Args:
        userid (int): Currently authenticating user ID.
        journalid (int): Character ID to fetch.
        rating (int): Maximum rating to display.
        ignore (bool): If should respect ignored or blocked tags.
        anyway (bool): If should ignore checks and display anyway.
        increment_views (bool): If should increment the number of views on the submission.

    Returns:
        A journal and all needed data.
    """

    query = d.engine.execute("""
        SELECT jo.userid, pr.username, jo.unixtime, jo.title, jo.rating, jo.settings, jo.page_views, pr.config
        FROM journal jo JOIN profile pr ON jo.userid = pr.userid
        WHERE jo.journalid = %(id)s
    """, id=journalid).fetchone()

    if journalid and userid in staff.MODS and anyway:
        pass
    elif not query or 'h' in query.settings:
        raise WeasylError('journalRecordMissing')
    elif query.rating > rating and ((userid != query.userid and userid not in staff.MODS) or d.is_sfw_mode()):
        raise WeasylError('RatingExceeded')
    elif 'f' in query.settings and not frienduser.check(userid, query.userid):
        raise WeasylError('FriendsOnly')
    elif ignore and ignoreuser.check(userid, query.userid):
        raise WeasylError('UserIgnored')
    elif ignore and blocktag.check(userid, journalid=journalid):
        raise WeasylError('TagBlocked')

    if increment_views and d.common_view_content(userid, journalid, 'journal'):
        query.page_views += 1

    return query


def select_view(userid, rating, journalid, ignore=True, anyway=None):
    journal = _select_journal_and_check(
        userid, journalid, rating=rating, ignore=ignore, anyway=anyway=='anyway')

    return {
        'journalid': journalid,
        'userid': journal.userid,
        'username': journal.username,
        'user_media': media.get_user_media(journal.userid),
        'mine': userid == journal.userid,
        'unixtime': journal.unixtime,
        'title': journal.title,
        'content': files.read(files.make_resource(userid, journalid, 'journal/submit')),
        'rating': journal.rating,
        'settings': journal.settings,
        'page_views': journal.page_views,
        'reported': report.check(journalid=journalid),
        'favorited': favorite.check(userid, journalid=journalid),
        'friends_only': 'f' in journal.settings,
        'hidden_submission': 'h' in journal.settings,
        'fave_count': favorite.count(journalid, 'journal'),
        'tags': searchtag.select(journalid=journalid),
        'comments': comment.select(userid, journalid=journalid),
    }


def select_view_api(userid, journalid, anyway=False, increment_views=False):
    rating = d.get_rating(userid)

    journal = _select_journal_and_check(userid, journalid,
        rating=rating, ignore=anyway, anyway=anyway, increment_views=increment_views)

    content = files.read(files.make_resource(userid, journalid, 'journal/submit'))

    return {
        'journalid': journalid,
        'title': journal.title,
        'owner': journal.username,
        'owner_login': d.get_sysname(journal.username),
        'content': text.markdown(content),
        'tags': searchtag.select(journalid=journalid),
        'link': d.absolutify_url('/journal/%d/%s' % (journalid, text.slug_for(journal.title))),
        'type': 'journal',
        'rating': ratings.CODE_TO_NAME[journal.rating],
        'views': journal.page_views,
        'favorites': favorite.count(journalid, 'journal'),
        'comments': comment.count(journalid, 'journal'),
        'favorited': favorite.check(userid, journalid=journalid),
        'friends_only': 'f' in journal.settings
    }


def select_query(userid, rating, otherid=None, backid=None, nextid=None, config=None):
    if config is None:
        config = d.get_config(userid)

    statement = [" FROM journal jo"
                 " JOIN profile pr ON jo.userid = pr.userid"
                 " WHERE jo.settings !~ 'h'"]

    if otherid:
        statement.append(" AND jo.userid = %i")

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" AND (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_FRIENDUSER_JOURNAL % (userid, userid, userid))

        if not otherid:
            statement.append(m.MACRO_IGNOREUSER % (userid, "jo"))

        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" AND jo.rating <= %i AND jo.settings !~ 'f'" % (rating,))

    if backid:
        statement.append(" AND jo.journalid > %i" % backid)
    elif nextid:
        statement.append(" AND jo.journalid < %i" % nextid)
    return statement


def select_user_count(userid, rating, otherid=None, backid=None, nextid=None, config=None):
    statement = ["SELECT count(jo.journalid)"]
    statement.extend(select_query(userid, rating, otherid, backid, nextid, config))
    return d.execute("".join(statement))[0][0]


def select_user_list(userid, rating, limit, otherid=None, backid=None, nextid=None, config=None):
    statement = ["SELECT jo.journalid, jo.title, jo.userid, pr.username, pr.config, jo.rating, jo.unixtime"]
    statement.extend(select_query(userid, rating, otherid, backid, nextid, config))
    statement.append(" ORDER BY jo.journalid%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = [{
        "contype": 30,
        "journalid": i[0],
        "title": i[1],
        "userid": i[2],
        "username": i[3],
        "rating": i[5],
        "unixtime": i[6],
    } for i in d.execute("".join(statement))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def select_list(userid, rating, limit, otherid=None, backid=None, nextid=None, config=None):
    if config is None:
        config = d.get_config(userid)

    statement = ["SELECT jo.journalid, jo.title, jo.unixtime FROM journal jo WHERE"]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        if not otherid:
            statement.append(m.MACRO_IGNOREUSER % (userid, "jo"))
        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" jo.rating <= %i" % (rating,))

    if otherid:
        statement.append(
            " AND jo.userid = %i AND jo.settings !~ '[%sh]'" % (otherid, "" if frienduser.check(userid, otherid) else "f"))
    else:
        statement.append(" AND jo.settings !~ 'h'")

    statement.append("ORDER BY jo.journalid DESC LIMIT %i" % limit)

    query = [{
        "journalid": i[0],
        "title": i[1],
        "unixtime": i[2],
    } for i in d.execute("".join(statement))]

    return query[::-1] if backid else query


def select_latest(userid, rating, otherid=None, config=None):
    if config is None:
        config = d.get_config(userid)

    statement = ["SELECT jo.journalid, jo.title, jo.unixtime FROM journal jo WHERE"]

    if userid:
        if d.is_sfw_mode():
            statement.append(" (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        if not otherid:
            statement.append(m.MACRO_IGNOREUSER % (userid, "jo"))
        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" jo.rating <= %i" % (rating,))

    if otherid:
        statement.append(
            " AND jo.userid = %i AND jo.settings !~ '[%sh]'" % (otherid, "" if frienduser.check(userid, otherid) else "f"))

    statement.append("ORDER BY jo.journalid DESC LIMIT 1")
    query = d.execute("".join(statement), options="single")

    if query:
        return {
            "journalid": query[0],
            "title": query[1],
            "unixtime": query[2],
            "content": files.read("%s%s%i.txt" % (m.MACRO_SYS_JOURNAL_PATH, d.get_hash_path(query[0]), query[0])),
            "comments": d.execute("SELECT COUNT(*) FROM journalcomment WHERE targetid = %i AND settings !~ 'h'",
                                  [query[0]], ["element"]),
        }


def edit(userid, journal, friends_only=False):
    if not journal.title:
        raise WeasylError("titleInvalid")
    elif not journal.content:
        raise WeasylError("contentInvalid")
    elif not journal.rating:
        raise WeasylError("ratingInvalid")
    profile.check_user_rating_allowed(userid, journal.rating)

    query = d.execute("SELECT userid, settings FROM journal WHERE journalid = %i", [journal.journalid], options="single")

    if not query or "h" in query[1]:
        raise WeasylError("Unexpected")
    elif userid != query[0] and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    settings = [query[1].replace("f", "")]
    settings.append("f" if friends_only else "")
    settings = "".join(settings)

    if "f" in settings:
        welcome.journal_remove(journal.journalid)

    # TODO(kailys): use ORM
    d.execute("UPDATE journal SET (title, rating, settings) = ('%s', %i, '%s') WHERE journalid = %i",
              [journal.title, journal.rating.code, settings, journal.journalid])

    # Write journal file
    files.write(files.make_resource(userid, journal.journalid, "journal/submit"),
                journal.content)

    if userid != query[0]:
        from weasyl import moderation
        moderation.note_about(
            userid, query[0], 'The following journal was edited:',
            '- ' + text.markdown_link(journal.title, '/journal/%s?anyway=true' % (journal.journalid,)))


def remove(userid, journalid):
    ownerid = d.get_ownerid(journalid=journalid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    query = d.execute("UPDATE journal SET settings = settings || 'h'"
                      " WHERE journalid = %i AND settings !~ 'h' RETURNING journalid", [journalid])

    if query:
        welcome.journal_remove(journalid)

    return ownerid

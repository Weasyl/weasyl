import arrow

from libweasyl import ratings
from libweasyl import staff
from libweasyl import text
from libweasyl.legacy import UNIXTIME_OFFSET

from weasyl import api
from weasyl import blocktag
from weasyl import comment
from weasyl import define as d
from weasyl import favorite
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import moderation
from weasyl import profile
from weasyl import report
from weasyl import searchtag
from weasyl import welcome
from weasyl.error import WeasylError
from weasyl.forms import NormalizedTag
from weasyl.users import Username


def create(
    userid: int,
    journal,
    *,
    friends_only: bool,
    tags: set[NormalizedTag],
) -> int:
    # Check invalid arguments
    if not journal.title:
        raise WeasylError("titleInvalid")
    elif not journal.content:
        raise WeasylError("contentInvalid")
    elif not journal.rating:
        raise WeasylError("ratingInvalid")
    profile.check_user_rating_allowed(userid, journal.rating)
    if journal.rating.minimum_age:
        profile.assert_adult(userid)

    # Create journal
    jo = d.meta.tables["journal"]

    journalid = d.engine.scalar(jo.insert().returning(jo.c.journalid), {
        "userid": userid,
        "title": journal.title,
        "content": journal.content,
        "rating": journal.rating.code,
        "unixtime": arrow.utcnow(),
        "hidden": False,
        "friends_only": friends_only,
        "submitter_ip_address": journal.submitter_ip_address,
        "submitter_user_agent_id": journal.submitter_user_agent_id,
    })

    # Assign search tags
    searchtag.associate(
        userid=userid,
        target=searchtag.JournalTarget(journalid),
        tag_names=tags,
    )

    # Create notifications
    welcome.journal_insert(userid, journalid, rating=journal.rating.code,
                           friends_only=friends_only)

    d.metric('increment', 'journals')
    d.cached_posts_count.invalidate(userid)

    return journalid


def _select_journal_and_check(
    userid,
    journalid,
    *,
    rating,
    ignore: bool,
    anyway: bool,
    increment_views: bool,
):
    """Selects a journal, after checking if the user is authorized, etc.

    Args:
        userid (int): Currently authenticating user ID.
        journalid (int): Journal ID to fetch.
        rating (int): Maximum rating to display.
        ignore: Whether to check for blocked tags and users.
        anyway: For moderators, whether to ignore checks (including permission checks and deleted status) and display anyway.
        increment_views: Whether to increment the number of views on the submission.

    Returns:
        A journal and all needed data as a dict.
    """

    query = d.engine.execute("""
        SELECT jo.userid, pr.username, jo.unixtime, jo.title, jo.content, jo.rating, jo.hidden, jo.friends_only, jo.page_views
        FROM journal jo JOIN profile pr ON jo.userid = pr.userid
        WHERE jo.journalid = %(id)s
    """, id=journalid).first()

    if query and userid in staff.MODS and anyway:
        pass
    elif not query or query.hidden:
        raise WeasylError('journalRecordMissing')
    elif query.rating > rating and ((userid != query.userid and userid not in staff.MODS) or d.is_sfw_mode()):
        raise WeasylError('RatingExceeded')
    elif query.friends_only and not frienduser.check(userid, query.userid):
        raise WeasylError('FriendsOnly')
    elif ignore and ignoreuser.check(userid, query.userid):
        raise WeasylError('UserIgnored')
    elif ignore and blocktag.check(userid, journalid=journalid):
        raise WeasylError('TagBlocked')

    query = dict(query)

    if increment_views and (new_views := d.common_view_content(userid, journalid, 'journals')) is not None:
        query['page_views'] = new_views

    return query


def select_view(
    userid,
    journalid,
    *,
    rating,
    ignore: bool = True,
    anyway: bool = False,
):
    journal = _select_journal_and_check(
        userid,
        journalid,
        rating=rating,
        ignore=ignore,
        anyway=anyway,
        increment_views=False,
    )

    return {
        'journalid': journalid,
        'userid': journal['userid'],
        'username': journal['username'],
        'user_media': media.get_user_media(journal['userid']),
        'mine': userid == journal['userid'],
        'unixtime': journal['unixtime'],
        'title': journal['title'],
        'content': journal['content'],
        'rating': journal['rating'],
        'page_views': journal['page_views'],
        'reported': report.check(journalid=journalid) if userid in staff.MODS else None,
        'favorited': favorite.check(userid, journalid=journalid),
        'friends_only': journal['friends_only'],
        'hidden': journal['hidden'],
        'fave_count': favorite.count(journalid, 'journal'),
        'tags': searchtag.select_grouped(userid, searchtag.JournalTarget(journalid)),
        'comments': comment.select(userid, journalid=journalid),
    }


def select_view_api(
    userid,
    journalid,
    *,
    anyway: bool,
    increment_views: bool,
):
    rating = d.get_rating(userid)

    journal = _select_journal_and_check(
        userid,
        journalid,
        rating=rating,
        ignore=not anyway,
        anyway=False,
        increment_views=increment_views,
    )

    username = Username.from_stored(journal['username'])

    return {
        'journalid': journalid,
        'title': journal['title'],
        'owner': username.display,
        'owner_login': username.sysname,
        'owner_media': api.tidy_all_media(
            media.get_user_media(journal['userid'])),
        'content': text.markdown(journal['content']),
        'tags': searchtag.select(journalid=journalid),
        'link': d.absolutify_url('/journal/%d/%s' % (journalid, text.slug_for(journal['title']))),
        'type': 'journal',
        'rating': ratings.CODE_TO_NAME[journal['rating']],
        'views': journal['page_views'],
        'favorites': favorite.count(journalid, 'journal'),
        'comments': comment.count(journalid, 'journal'),
        'favorited': favorite.check(userid, journalid=journalid),
        'friends_only': journal['friends_only'],
        'posted_at': d.iso8601(journal['unixtime']),
    }


def select_user_list(userid, rating, limit, backid=None, nextid=None):
    statement = [
        "SELECT jo.journalid, jo.title, jo.userid, pr.username, jo.rating, jo.unixtime, jo.content"
        " FROM journal jo"
        " JOIN profile pr ON jo.userid = pr.userid"
        " WHERE NOT jo.hidden"]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" AND (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_FRIENDUSER_JOURNAL % (userid, userid, userid))
        statement.append(m.MACRO_IGNOREUSER % (userid, "jo"))
        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" AND jo.rating <= %i AND NOT jo.friends_only" % (rating,))

    if backid:
        statement.append(" AND jo.journalid > %i" % backid)
    elif nextid:
        statement.append(" AND jo.journalid < %i" % nextid)

    statement.append(" ORDER BY jo.journalid%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = [{
        "contype": 30,
        "journalid": i[0],
        "title": i[1],
        "userid": i[2],
        "username": i[3],
        "rating": i[4],
        "unixtime": i[5],
        "content": i.content,
    } for i in d.execute("".join(statement))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def select_list(userid, rating, otherid):
    statement = ["SELECT jo.journalid, jo.title, jo.unixtime, jo.rating, jo.content FROM journal jo WHERE"]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" jo.rating <= %i" % (rating,))

    statement.append(" AND jo.userid = %i AND NOT jo.hidden" % (otherid,))

    if not frienduser.check(userid, otherid):
        statement.append(" AND NOT jo.friends_only")

    statement.append(" ORDER BY jo.journalid DESC")

    return [{
        "journalid": i.journalid,
        "title": i.title,
        "created_at": arrow.get(i.unixtime - UNIXTIME_OFFSET),
        "rating": i.rating,
        "content": i.content,
    } for i in d.engine.execute("".join(statement)).fetchall()]


def select_latest(userid, rating, otherid):
    statement = ["SELECT jo.journalid, jo.title, jo.content, jo.unixtime FROM journal jo WHERE"]

    if userid:
        if d.is_sfw_mode():
            statement.append(" (jo.rating <= %i)" % (rating,))
        else:
            statement.append(" (jo.userid = %i OR jo.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_BLOCKTAG_JOURNAL % (userid, userid))
    else:
        statement.append(" jo.rating <= %i" % (rating,))

    statement.append(" AND jo.userid = %i AND NOT jo.hidden" % (otherid,))

    if not frienduser.check(userid, otherid):
        statement.append(" AND NOT jo.friends_only")

    statement.append(" ORDER BY jo.journalid DESC LIMIT 1")
    query = d.engine.execute("".join(statement)).first()

    if query:
        return {
            "journalid": query.journalid,
            "title": query.title,
            "content": query.content,
            "unixtime": query.unixtime,
            "comments": d.engine.scalar(
                "SELECT count(*) FROM journalcomment WHERE targetid = %(journal)s AND settings !~ 'h'",
                journal=query.journalid,
            ),
        }


def edit(userid: int, journal, *, friends_only: bool) -> None:
    if not journal.title:
        raise WeasylError("titleInvalid")
    elif not journal.content:
        raise WeasylError("contentInvalid")
    elif not journal.rating:
        raise WeasylError("ratingInvalid")

    query = d.engine.execute(
        "SELECT userid, hidden FROM journal WHERE journalid = %(id)s",
        id=journal.journalid,
    ).first()

    if not query or query.hidden:
        raise WeasylError("Unexpected")
    elif userid != query[0] and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    if userid == query.userid:
        profile.check_user_rating_allowed(userid, journal.rating)
        if journal.rating.minimum_age:
            profile.assert_adult(userid)

    if friends_only:
        welcome.journal_remove(journal.journalid)

    jo = d.meta.tables['journal']
    d.engine.execute(
        jo.update()
        .where(jo.c.journalid == journal.journalid)
        .values({
            'title': journal.title,
            'content': journal.content,
            'rating': journal.rating,
            'friends_only': friends_only,
        })
    )

    if userid != query[0]:
        moderation.note_about(
            userid, query[0], 'The following journal was edited:',
            '- ' + text.markdown_link(journal.title, '/journal/%s?anyway=true' % (journal.journalid,)))

    d.cached_posts_count.invalidate(query[0])


def remove(userid: int, journalid: int) -> int | None:
    ownerid = d.get_ownerid(journalid=journalid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    result = d.engine.execute(
        "UPDATE journal SET hidden = TRUE WHERE journalid = %(journalid)s AND NOT hidden",
        {"journalid": journalid},
    )

    if result.rowcount != 0:
        welcome.journal_remove(journalid)
        d.cached_posts_count.invalidate(ownerid)

    return ownerid

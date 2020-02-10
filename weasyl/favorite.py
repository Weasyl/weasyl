from __future__ import absolute_import

from weasyl import collection
from weasyl import define as d
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


def select_submit_query(userid, rating, otherid=None, backid=None, nextid=None):
    statement = [
        " FROM favorite fa INNER JOIN"
        " submission su ON fa.targetid = su.submitid"
        " INNER JOIN profile pr ON su.userid = pr.userid"
        " WHERE fa.type = 's' AND su.settings !~ 'h'"]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" AND (su.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (su.userid = %i OR su.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_IGNOREUSER % (userid, "su"))
        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))
    else:
        statement.append(" AND su.rating <= %i" % (rating,))
        statement.append(" AND su.settings !~ 'f'")

    statement.append(" AND fa.userid = %i" % otherid)

    if backid:
        statement.append(" AND fa.unixtime > "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 's'))"
                         % (otherid, backid))
    elif nextid:
        statement.append(" AND fa.unixtime < "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 's'))"
                         % (otherid, nextid))

    return statement


def select_submit_count(userid, rating, otherid, backid=None, nextid=None):
    statement = ["SELECT COUNT(submitid) "]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid))
    return d.execute("".join(statement))[0][0]


def select_submit(userid, rating, limit, otherid, backid=None, nextid=None):
    statement = ["SELECT su.submitid, su.title, su.rating, fa.unixtime, su.userid, pr.username, su.subtype"]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid))

    statement.append(" ORDER BY fa.unixtime%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = [{
        "contype": 10,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "subtype": i[6],
    } for i in d.execute("".join(statement))]
    media.populate_with_submission_media(query)

    return query[::-1] if backid else query


def select_char(userid, rating, limit, otherid, backid=None, nextid=None):
    statement = ["""
        SELECT ch.charid, ch.char_name, ch.rating, fa.unixtime, ch.userid, pr.username, ch.settings
        FROM favorite fa
            INNER JOIN character ch ON fa.targetid = ch.charid
            INNER JOIN profile pr ON ch.userid = pr.userid
        WHERE fa.type = 'f'
            AND ch.settings !~ 'h'
    """]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" AND (ch.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (ch.userid = %i OR ch.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_FRIENDUSER_CHARACTER % (userid, userid, userid))
        statement.append(m.MACRO_IGNOREUSER % (userid, "ch"))
        statement.append(m.MACRO_BLOCKTAG_CHAR % (userid, userid))
    else:
        statement.append(" AND ch.rating <= %i AND ch.settings !~ 'f'" % (rating,))

    statement.append(" AND fa.userid = %i" % (otherid,))

    if backid:
        statement.append(" AND fa.unixtime > "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 'f'))"
                         % (otherid, backid))
    elif nextid:
        statement.append(" AND fa.unixtime < "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 'f'))"
                         % (otherid, nextid))

    statement.append(" ORDER BY fa.unixtime%s LIMIT %i" % ("" if backid else " DESC", limit))

    from weasyl import character
    query = [{
        "contype": 20,
        "charid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "sub_media": character.fake_media_items(i[0], i[4], d.get_sysname(i[5]), i[6]),
    } for i in d.execute("".join(statement))]

    return query[::-1] if backid else query


def select_journal(userid, rating, limit, otherid, backid=None, nextid=None):
    statement = ["""
        SELECT jo.journalid, jo.title, jo.rating, fa.unixtime, jo.userid, pr.username, pr.config
        FROM favorite fa
            INNER JOIN journal jo ON fa.targetid = jo.journalid
            INNER JOIN profile pr ON jo.userid = pr.userid
        WHERE fa.type = 'j'
            AND jo.settings !~ 'h'
    """]

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
        statement.append(" AND jo.rating <= %i AND jo.settings !~ 'f'" % (rating,))

    statement.append(" AND fa.userid = %i" % (otherid,))

    if backid:
        statement.append(" AND fa.unixtime > "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 'j'))"
                         % (otherid, backid))
    elif nextid:
        statement.append(" AND fa.unixtime < "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 'j'))"
                         % (otherid, nextid))

    statement.append(" ORDER BY fa.unixtime%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = [{
        "contype": 30,
        "journalid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
    } for i in d.execute("".join(statement))]
    media.populate_with_user_media(query)

    return query[::-1] if backid else query


def insert(userid, submitid=None, charid=None, journalid=None):
    if submitid:
        content_table, id_field, target = "submission", "submitid", submitid
    elif charid:
        content_table, id_field, target = "character", "charid", charid
    else:
        content_table, id_field, target = "journal", "journalid", journalid

    query = d.engine.execute(
        "SELECT userid, settings FROM %s WHERE %s = %i" % (content_table, id_field, target),
    ).first()

    if not query:
        raise WeasylError("TargetRecordMissing")
    elif userid == query[0]:
        raise WeasylError("CannotSelfFavorite")
    elif "f" in query[1] and not frienduser.check(userid, query[0]):
        raise WeasylError("FriendsOnly")
    elif ignoreuser.check(userid, query[0]):
        raise WeasylError("YouIgnored")
    elif ignoreuser.check(query[0], userid):
        raise WeasylError("contentOwnerIgnoredYou")

    notified = []

    def insert_transaction(db):
        insert_result = db.execute(
            'INSERT INTO favorite (userid, targetid, type, unixtime) '
            'VALUES (%(user)s, %(target)s, %(type)s, %(now)s) '
            'ON CONFLICT DO NOTHING',
            user=userid,
            target=d.get_targetid(submitid, charid, journalid),
            type='s' if submitid else 'f' if charid else 'j',
            now=d.get_time())

        if insert_result.rowcount == 0:
            return

        if submitid:
            db.execute(
                """
                UPDATE submission SET
                    favorites = (
                        CASE
                            WHEN favorites IS NULL THEN
                                (SELECT count(*) FROM favorite WHERE type = 's' AND targetid = %(target)s)
                            ELSE
                                favorites + 1
                        END
                    )
                    WHERE submitid = %(target)s
                """,
                target=submitid,
            )

        if not notified:
            # create a list of users to notify
            notified_ = collection.find_owners(submitid)

            # conditions under which "other" should be notified
            def can_notify(other):
                other_jsonb = d.get_profile_settings(other)
                allow_notify = other_jsonb.allow_collection_notifs
                return allow_notify and not ignoreuser.check(other, userid)
            notified.extend(u for u in notified_ if can_notify(u))
            # always notify for own content
            notified.append(query[0])

        for other in notified:
            welcome.favorite_insert(db, userid, submitid=submitid, charid=charid, journalid=journalid, otherid=other)

    d.serializable_retry(insert_transaction)


def remove(userid, submitid=None, charid=None, journalid=None):
    def remove_transaction(db):
        delete_result = db.execute(
            "DELETE FROM favorite WHERE (userid, targetid, type) = (%(user)s, %(target)s, %(type)s)",
            user=userid,
            target=d.get_targetid(submitid, charid, journalid),
            type="s" if submitid else "f" if charid else "j",
        )

        if delete_result.rowcount == 0:
            return

        if submitid:
            db.execute(
                "UPDATE submission SET favorites = favorites - 1 WHERE submitid = %(target)s",
                target=submitid,
            )

        welcome.favorite_remove(db, userid, submitid=submitid, charid=charid, journalid=journalid)

    d.serializable_retry(remove_transaction)


def check(userid, submitid=None, charid=None, journalid=None):
    if not userid:
        return False

    return d.engine.scalar(
        """
            SELECT EXISTS (
                SELECT 0 FROM favorite
                    WHERE (userid, targetid, type) = (%(user)s, %(target)s, %(type)s)
            )
        """,
        user=userid,
        target=d.get_targetid(submitid, charid, journalid),
        type="s" if submitid else "f" if charid else "j",
    )


def count(id, contenttype='submission'):
    """Fetches the count of favorites on some content.

    Args:
        id (int): ID of the content to get the count for.
        contenttype (str): Type of content to fetch. It accepts one of the following:
            submission, journal, or character

    Returns:
        An int with the number of favorites.
    """

    if contenttype == 'submission':
        querytype = 's'
    elif contenttype == 'journal':
        querytype = 'j'
    elif contenttype == 'character':
        querytype = 'f'
    else:
        raise ValueError("type should be one of 'submission', 'journal', or 'character'")

    return d.engine.scalar(
        "SELECT COUNT(*) FROM favorite WHERE targetid = %s AND type = %s",
        (id, querytype))

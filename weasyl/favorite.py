# favorite.py

from error import PostgresError, WeasylError
import macro as m
import define as d

import welcome
import frienduser
import ignoreuser
import collection

from weasyl import media


def select_submit_query(userid, rating, otherid=None, backid=None, nextid=None, config=None):
    if config is None:
        config = d.get_config(userid)

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

    if otherid:
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


def select_submit_count(userid, rating, otherid=None, backid=None, nextid=None, config=None):
    statement = ["SELECT COUNT(submitid) "]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid, config))
    return d.execute("".join(statement))[0][0]


def select_submit(userid, rating, limit, otherid=None, backid=None, nextid=None, config=None):
    statement = ["SELECT su.submitid, su.title, su.rating, fa.unixtime, su.userid, pr.username, su.subtype"]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid, config))

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


def select_char(userid, rating, limit, otherid=None, backid=None, nextid=None, config=None):
    if config is None:
        config = d.get_config(userid)
    query = []
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

    if otherid:
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


def select_journal(userid, rating, limit, otherid=None, backid=None, nextid=None, config=None):
    if config is None:
        config = d.get_config(userid)
    query = []
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

    if otherid:
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

    query = d.execute("SELECT userid, settings FROM %s WHERE %s = %i",
                      [content_table, id_field, target], options="single")

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

    try:
        d.execute("INSERT INTO favorite VALUES (%i, %i, '%s', %i)", [
            userid, d.get_targetid(submitid, charid, journalid),
            "s" if submitid else "f" if charid else "j", d.get_time()
        ])
    except PostgresError:
        raise WeasylError("favoriteRecordExists")

    # create a list of users to notify
    notified = set(collection.find_owners(submitid))

    # conditions under which "other" should be notified
    def can_notify(other):
        other_jsonb = d.get_profile_settings(other)
        allow_notify = other_jsonb.allow_collection_notifs
        not_ignored = not ignoreuser.check(other, userid)
        return allow_notify and not_ignored
    notified = set(filter(can_notify, notified))
    # always notify for own content
    notified.add(query[0])

    for other in notified:
        welcome.favorite_insert(userid, submitid=submitid, charid=charid, journalid=journalid, otherid=other)


def remove(userid, submitid=None, charid=None, journalid=None):
    d.execute("DELETE FROM favorite WHERE (userid, targetid, type) = (%i, %i, '%s')",
              [userid, d.get_targetid(submitid, charid, journalid), "s" if submitid else "f" if charid else "j"])

    welcome.favorite_remove(userid, submitid=submitid, charid=charid, journalid=journalid)


def check(userid, submitid=None, charid=None, journalid=None):
    if not userid:
        return False

    return d.execute(
        """
            SELECT EXISTS (
                SELECT 0 FROM favorite
                    WHERE (userid, targetid, type) = (%i, %i, '%s')
            )
        """, [
            userid, d.get_targetid(submitid, charid, journalid),
            "s" if submitid else "f" if charid else "j"
        ], options="bool")


def count(submitid=None, journalid=None):
    return d.execute(
        "SELECT COUNT(*) FROM favorite WHERE targetid = %i AND type = '%s'",
        [submitid, 's' if submitid else 'j'], options=['element'])

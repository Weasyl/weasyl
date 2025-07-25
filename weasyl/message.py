from itertools import chain

from weasyl import character
from weasyl import define as d
from weasyl import media


notification_clusters = {
    1010: 0, 1015: 0,
    3010: 1,
    3020: 2, 3100: 2, 3110: 2, 3050: 2,
    3030: 3, 3040: 3,

    3070: 5, 3075: 5,
    3080: 6,
    3085: 7,
    3140: 8,
    4010: 8, 4015: 8,
    4016: 9,
    4020: 10, 4025: 10, 4050: 10,
    4030: 11, 4035: 11, 4060: 11, 4065: 11,
    4040: 12, 4045: 12,
}

_CONTYPE_CHAR = 20


def _fake_media_items(i):
    if i.contype == _CONTYPE_CHAR:
        return character.fake_media_items(
            i.id,
            i.userid,
            d.get_sysname(i.username),
            i.settings)
    else:
        return None


def remove(userid, messages):
    if not messages:
        return

    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND welcomeid = ANY (%(remove)s)",
        user=userid, remove=messages)

    d._page_header_info.invalidate(userid)


def remove_all_before(userid, before):
    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND type = ANY (%(types)s) AND unixtime < %(before)s",
        user=userid, types=list(notification_clusters), before=before)

    d._page_header_info.invalidate(userid)


def remove_all_submissions(userid, only_before):
    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND type IN (2010, 2030, 2040, 2050) AND unixtime < %(before)s",
        user=userid, before=only_before)

    d._page_header_info.invalidate(userid)


def select_journals(userid):
    journals = d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.targetid, pr.username, jo.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN journal jo ON we.targetid = jo.journalid
        WHERE
            (we.userid, we.type) = (%(user)s, 1010) AND
            rating <= %(rating)s
        ORDER BY we.unixtime DESC
    """, user=userid, rating=d.get_rating(userid))

    return [{
        "type": 1010,
        "id": j.welcomeid,
        "unixtime": j.unixtime,
        "userid": j.otherid,
        "username": j.username,
        "journalid": j.targetid,
        "title": j.title,
    } for j in journals]


def select_submissions(userid, limit, include_tags, backtime=None, nexttime=None):
    if backtime:
        time_filter = "AND we.unixtime > %(backtime)s"
    elif nexttime:
        time_filter = "AND we.unixtime < %(nexttime)s"
    else:
        time_filter = ""

    if include_tags:
        char_tags_select = ", COALESCE(array_agg(tagid) FILTER (WHERE tagid IS NOT NULL), '{}') AS tags"
        char_tags_join = "LEFT JOIN searchmapchar AS smc ON ch.charid = smc.targetid"
        char_tags_groupby = "GROUP BY ch.charid, pr.username, we.welcomeid"

        submission_tags_select = ", tags"
        submission_tags_join = "INNER JOIN submission_tags USING (submitid)"
    else:
        char_tags_select = char_tags_join = char_tags_groupby = submission_tags_select = submission_tags_join = ""

    statement = """
        SELECT * FROM (
            SELECT
                20 AS contype,
                ch.charid AS id,
                ch.char_name AS title,
                ch.rating,
                we.unixtime,
                ch.userid,
                pr.username,
                ch.settings,
                we.welcomeid,
                0 AS subtype
                {char_tags_select}
            FROM welcome we
                INNER JOIN character ch ON we.targetid = ch.charid
                INNER JOIN profile pr ON ch.userid = pr.userid
                {char_tags_join}
            WHERE
                we.type = 2050 AND
                we.userid = %(userid)s AND
                ch.rating <= %(rating)s
                {time_filter}
            {char_tags_groupby}
            ORDER BY welcomeid DESC LIMIT %(limit)s
        ) t
        UNION ALL SELECT * FROM (
            SELECT
                40 AS contype,
                su.submitid AS id,
                su.title,
                su.rating,
                we.unixtime,
                we.otherid AS userid,
                pr.username,
                ''::text AS settings,
                we.welcomeid,
                su.subtype
                {submission_tags_select}
            FROM welcome we
                INNER JOIN submission su ON we.targetid = su.submitid
                INNER JOIN profile pr ON we.otherid = pr.userid
                {submission_tags_join}
            WHERE
                we.type = 2030 AND
                we.userid = %(userid)s AND
                su.rating <= %(rating)s
                {time_filter}
            ORDER BY welcomeid DESC LIMIT %(limit)s
        ) t
        UNION ALL SELECT * FROM (
            SELECT
                10 AS contype,
                su.submitid AS id,
                su.title,
                su.rating,
                we.unixtime,
                su.userid,
                pr.username,
                ''::text AS settings,
                we.welcomeid,
                su.subtype
                {submission_tags_select}
            FROM welcome we
                INNER JOIN submission su ON we.targetid = su.submitid
                INNER JOIN profile pr ON su.userid = pr.userid
                {submission_tags_join}
            WHERE
                we.type = 2010 AND
                we.userid = %(userid)s AND
                su.rating <= %(rating)s
                {time_filter}
            ORDER BY welcomeid DESC LIMIT %(limit)s
        ) t
        ORDER BY welcomeid DESC LIMIT %(limit)s
    """.format(
        time_filter=time_filter,
        char_tags_select=char_tags_select,
        char_tags_join=char_tags_join,
        char_tags_groupby=char_tags_groupby,
        submission_tags_select=submission_tags_select,
        submission_tags_join=submission_tags_join,
    )

    query = d.engine.execute(
        statement,
        userid=userid,
        rating=d.get_rating(userid),
        nexttime=nexttime,
        backtime=backtime,
        limit=limit,
    ).fetchall()

    if include_tags:
        all_tags = list(frozenset(chain.from_iterable(i.tags for i in query)))
        tag_map = {t.tagid: t.title for t in d.engine.execute("SELECT tagid, title FROM searchtag WHERE tagid = ANY (%(tags)s)", tags=all_tags)}

        results = [{
            "contype": i.contype,
            "submitid" if i.contype != _CONTYPE_CHAR else "charid": i.id,
            "welcomeid": i.welcomeid,
            "title": i.title,
            "rating": i.rating,
            "unixtime": i.unixtime,
            "userid": i.userid,
            "username": i.username,
            "subtype": i.subtype,
            "tags": [tag_map[tag] for tag in i.tags],
            "sub_media": _fake_media_items(i),
        } for i in query]
    else:
        results = [{
            "contype": i.contype,
            "submitid" if i.contype != _CONTYPE_CHAR else "charid": i.id,
            "welcomeid": i.welcomeid,
            "title": i.title,
            "rating": i.rating,
            "unixtime": i.unixtime,
            "userid": i.userid,
            "username": i.username,
            "subtype": i.subtype,
            "sub_media": _fake_media_items(i),
        } for i in query]

    media.populate_with_submission_media(
        [i for i in results if i["contype"] != _CONTYPE_CHAR])

    return results


def select_notifications(userid):
    queries = []

    # Streaming
    queries.append({
        "type": i.type,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "stream_url": i.stream_url,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.type, we.unixtime, we.otherid, pr.username, pr.stream_url
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type IN (3070, 3075)
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Collection offers to user
    queries.append({
        "type": i.type,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.targetid,
        "title": i.title,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.type, we.unixtime, we.otherid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.targetid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type IN (3030, 3035)
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Following
    queries.append({
        "type": 3010,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3010
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Friend requests
    queries.append({
        "type": 3080,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3080
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Friend confirmations
    queries.append({
        "type": 3085,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3085
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Favorite
    for t, id_field, title_field, table_name in [(3020, "submitid", "title", "submission"),
                                                 (3050, "submitid", "title", "submission"),
                                                 (3100, "charid", "char_name", "character"),
                                                 (3110, "journalid", "title", "journal")]:
        queries.append([{
            "type": t,
            "id": i.welcomeid,
            "unixtime": i.unixtime,
            "userid": i.otherid,
            "username": i.username,
            id_field: i.id,
            "title": i.title,
        } for i in d.engine.execute("""
            SELECT
                we.welcomeid, we.unixtime, we.otherid, pr.username, {table}.{id_field}
                AS id, {table}.{title_field} AS title
            FROM welcome we
                INNER JOIN profile pr ON we.otherid = pr.userid
                INNER JOIN {table} ON we.referid = {table}.{id_field}
            WHERE we.userid = %(user)s
                AND we.type = %(type)s
            ORDER BY we.unixtime DESC
        """.format(id_field=id_field, title_field=title_field, table=table_name), type=t, user=userid)])

    # User changed submission tags
    queries.append({
        "type": 3140,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "submitid": i.submitid,
        "title": i.title,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, su.submitid, su.title
        FROM welcome we
            INNER JOIN submission su ON we.otherid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 3140
        ORDER BY we.unixtime DESC
    """, user=userid))

    return list(chain(*queries))


def select_comments(userid):
    queries = []

    # Shout comments
    current_username = d.get_sysname(d.get_display_name(userid))
    queries.append({
        "type": 4010,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownername": current_username,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.targetid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 4010
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Shout replies
    queries.append({
        "type": 4015,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownerid": i.ownerid,
        "ownername": i.owner_username,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT
            we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, px.userid AS ownerid,
            px.username AS owner_username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sh ON we.referid = sh.commentid
            INNER JOIN profile px ON sh.target_user = px.userid
        WHERE we.userid = %(user)s
            AND we.type = 4015
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Staff comment replies
    queries.append({
        "type": 4016,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownerid": i.ownerid,
        "ownername": i.owner_username,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT
            we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, px.userid AS ownerid,
            px.username AS owner_username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sh ON we.referid = sh.commentid
            INNER JOIN profile px ON sh.target_user = px.userid
        WHERE we.userid = %(user)s
            AND we.type = 4016
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Submission comments
    queries.append({
        "type": 4020,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4020
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Submission comment replies
    queries.append({
        "type": 4025,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.submitid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.submitid, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sc ON we.referid = sc.commentid
            INNER JOIN submission su ON sc.target_sub = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4025
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Character comments
    queries.append({
        "type": 4040,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "charid": i.referid,
        "title": i.char_name,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, ch.char_name
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN character ch ON we.referid = ch.charid
        WHERE we.userid = %(user)s
            AND we.type = 4040
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Character comment replies
    queries.append({
        "type": 4045,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "charid": i.charid,
        "title": i.char_name,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, ch.charid, ch.char_name
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN charcomment cc ON we.referid = cc.commentid
            INNER JOIN character ch ON cc.targetid = ch.charid
        WHERE we.userid = %(user)s
            AND we.type = 4045
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Journal comments
    queries.append({
        "type": 4030,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "journalid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, jo.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN journal jo ON we.referid = jo.journalid
        WHERE we.userid = %(user)s
            AND we.type = 4030
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Journal comment replies
    queries.append({
        "type": 4035,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "journalid": i.journalid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, jo.journalid, jo.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN journalcomment jc ON we.referid = jc.commentid
            INNER JOIN journal jo ON jc.targetid = jo.journalid
        WHERE we.userid = %(user)s
            AND we.type = 4035
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Site update comments
    queries.append({
        "type": 4060,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "updateid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, up.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN siteupdate up ON we.referid = up.updateid
        WHERE we.userid = %(user)s
            AND we.type = 4060
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Site update comment replies
    queries.append({
        "type": 4065,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "updateid": i.updateid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, up.updateid, up.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN siteupdatecomment uc ON we.referid = uc.commentid
            INNER JOIN siteupdate up ON uc.targetid = up.updateid
        WHERE we.userid = %(user)s
            AND we.type = 4065
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Collection comments
    queries.append({
        "type": 4050,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4050
        ORDER BY we.unixtime DESC
    """, user=userid))

    return list(chain(*queries))

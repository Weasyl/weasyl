from weasyl import define as d
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError


def select_query(userid, *, rating, otherid, pending=False, backid=None, nextid=None):
    """
    Build a query to select a list of collections, joined on submission table
    and profile of the submitter
    :param userid: the user accessing this content.
    :param rating: maximum rating of collections to display
    :param otherid: the owner of the collections being accessed (collector)
    :param pending: TRUE to give only pending collections, otherwise give accepted ones.
    :param backid: will not return submissions older than the one with this ID
    :param nextid: will not return submissions newer than the one with this ID
    :return: a statement created based on options given
    """
    statement = [
        "FROM collection co INNER JOIN"
        " submission su ON co.submitid = su.submitid"
        " INNER JOIN profile pr ON su.userid = pr.userid"
        " INNER JOIN profile cpr ON co.userid = cpr.userid"
        " WHERE NOT su.hidden"]

    # filter own content in SFW mode
    if d.is_sfw_mode():
        statement.append(" AND (su.rating <= %i)" % (rating,))
    else:
        statement.append(" AND (su.rating <= %i OR co.userid = %i OR su.userid = %i)" % (rating, userid, userid))

    if pending:
        # in the case of pending, for OFFERED (p) show those collected by me
        # for REQUESTED (r) show those authored by me
        statement.append(" AND ((co.settings ~ 'p' AND co.userid = %i)"
                         " OR (co.settings ~ 'r' AND su.userid = %i))"
                         % (otherid, userid))
    else:
        statement.append(" AND co.settings !~ '[pr]'")
        statement.append(" AND co.userid = %i" % otherid)

    if backid:
        statement.append(" AND co.unixtime > (SELECT unixtime FROM collection WHERE (userid, submitid) = (%i, %i))"
                         % (otherid, backid))
    elif nextid:
        statement.append(" AND co.unixtime < (SELECT unixtime FROM collection WHERE (userid, submitid) = (%i, %i))"
                         % (otherid, nextid))

    if userid:
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))

        if not otherid:
            statement.append(m.MACRO_IGNOREUSER % (userid, "su"))

        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
    else:
        statement.append(" AND NOT su.friends_only")
    return statement


def select_count(userid, rating, *, otherid, pending=False, backid=None, nextid=None):
    statement = ["SELECT count(su.submitid) "]
    statement.extend(select_query(userid, rating=rating, otherid=otherid, pending=pending,
                                  backid=backid, nextid=nextid))
    return d.execute("".join(statement))[0][0]


def select_list(userid, rating, limit, *, otherid, pending=False, backid=None, nextid=None):
    statement = ["SELECT su.submitid, su.title, su.subtype, su.rating, co.unixtime, "
                 "su.userid, pr.username, cpr.username, cpr.userid "]
    statement.extend(select_query(userid, rating=rating, otherid=otherid, pending=pending,
                                  backid=backid, nextid=nextid))
    statement.append(" ORDER BY co.unixtime%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = []
    for i in d.execute("".join(statement)):
        query.append({
            "contype": 10,
            "collection": True,
            "submitid": i[0],
            "title": i[1],
            "subtype": i[2],
            "rating": i[3],
            "unixtime": i[4],
            "userid": i[5],
            "username": i[6],  # username of creator
            "collector": i[7],  # username of collector
            "collectorid": i[8],
            "sub_media": media.get_submission_media(i[0]),
        })

    return query[::-1] if backid else query


def find_owners(submitid):
    """
    Retrieve a list of users who have collected the given submission.
    does NOT include the original submitter.
    :param submitid: any submission ID
    :return: a list of userids of all users who have collected this submission
    """
    result = d.engine.execute(
        "SELECT userid FROM collection WHERE submitid = %(sub)s AND settings !~ '[pr]'",
        sub=submitid)
    return [r[0] for r in result]


def owns(userid, submitid):
    if not userid:
        return False

    return d.engine.scalar(
        "SELECT EXISTS (SELECT FROM collection WHERE userid = %(user)s AND submitid = %(sub)s)",
        user=userid,
        sub=submitid,
    )


def offer(userid, submitid, otherid):
    query = d.engine.execute(
        "SELECT userid, hidden, friends_only FROM submission WHERE submitid = %(id)s",
        id=submitid,
    ).first()

    if not query or query.hidden:
        raise WeasylError("Unexpected")
    if userid != query.userid:
        raise WeasylError("Unexpected")

    # Check collection acceptability
    if query.friends_only:
        raise WeasylError("collectionUnacceptable")
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    if ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")

    result = d.engine.execute(
        "INSERT INTO collection (userid, submitid, unixtime, settings)"
        " VALUES (%(userid)s, %(submitid)s, %(now)s, %(settings)s)"
        " ON CONFLICT (userid, submitid) DO NOTHING",
        userid=otherid,
        submitid=submitid,
        now=d.get_time(),
        settings="p",
    )

    if result.rowcount == 0:
        raise WeasylError("collectionExists")

    welcome.collectoffer_insert(userid, otherid, submitid)


def _check_throttle(userid, otherid):
    """
    Determine whether the user has been sending
    way too many (10 unapproved) collection requests.
    :param userid: the user making the requests
    :param otherid: the user the requests are to
    :return: TRUE if the user should be throttled, otherwise false
    """
    return d.engine.scalar(
        "SELECT count(*) > 10 FROM collection c "
        "JOIN submission s ON s.submitid = c.submitid "
        "WHERE s.userid = %(other)s AND c.userid = %(user)s "
        "AND c.settings ~ 'r'",
        other=otherid, user=userid)


def request(userid, submitid, otherid):
    query = d.engine.execute("SELECT userid, rating, hidden, friends_only "
                             "FROM submission WHERE submitid = %(submission)s",
                             submission=submitid).first()

    rating = d.get_rating(userid)

    if not query or query.hidden:
        raise WeasylError("Unexpected")
    if otherid != query.userid:
        raise WeasylError("Unexpected")

    # not checking for blocktags here because if you want to collect
    # something with a tag you don't like that's your business
    if rating < query.rating:
        raise WeasylError("RatingExceeded")
    if query.friends_only:
        raise WeasylError("collectionUnacceptable")
    if ignoreuser.check(otherid, userid):
        raise WeasylError("IgnoredYou")
    if ignoreuser.check(userid, otherid):
        raise WeasylError("YouIgnored")
    if _check_throttle(userid, otherid):
        raise WeasylError("collectionThrottle")

    settings = d.get_profile_settings(otherid)
    if not settings.allow_collection_requests:
        raise WeasylError("Unexpected")

    result = d.engine.execute(
        "INSERT INTO collection (userid, submitid, unixtime, settings)"
        " VALUES (%(userid)s, %(submitid)s, %(now)s, %(settings)s)"
        " ON CONFLICT (userid, submitid) DO NOTHING",
        userid=userid,
        submitid=submitid,
        now=d.get_time(),
        settings="r",
    )

    if result.rowcount == 0:
        raise WeasylError("collectionExists")

    welcome.collectrequest_insert(userid, otherid, submitid)


def pending_accept(userid, submissions):
    if not submissions:
        return

    updated = d.engine.execute(
        "UPDATE collection SET"
        " unixtime = %(now)s,"
        " settings = REGEXP_REPLACE(collection.settings, '[pr]', '')"
        " FROM submission WHERE collection.submitid = submission.submitid"
        " AND %(userid)s IN (collection.userid, submission.userid)"
        " AND (collection.submitid, collection.userid) = ANY (%(submissions)s)"
        " AND collection.settings ~ (CASE WHEN %(userid)s = collection.userid THEN 'p' ELSE 'r' END)"
        " RETURNING collection.userid, collection.submitid",
        userid=userid,
        submissions=submissions,
        now=d.get_time(),
    ).fetchall()

    for s in updated:
        welcome.collection_insert(s[1], s[0])
        welcome.collectrequest_remove(userid, s[1], s[0])

    d._page_header_info.invalidate(userid)
    d.cached_posts_count.invalidate(userid)


def pending_reject(userid, submissions):
    if not submissions:
        return

    d.engine.execute(
        "DELETE FROM collection"
        " USING submission WHERE collection.submitid = submission.submitid"
        " AND %(userid)s IN (collection.userid, submission.userid)"
        " AND (collection.submitid, collection.userid) = ANY (%(submissions)s)"
        " AND collection.settings ~ (CASE WHEN %(userid)s = collection.userid THEN 'p' ELSE 'r' END)",
        userid=userid,
        submissions=submissions,
    )

    for submitid, collectorid in submissions:
        welcome.collectrequest_remove(userid, collectorid, submitid)

    d._page_header_info.invalidate(userid)


def remove(userid, submissions):
    if not submissions:
        return

    d.engine.execute("""
        DELETE FROM collection
        WHERE userid = %(user)s
            AND submitid = ANY (%(submissions)s)
            AND settings !~ '[pr]'
    """, user=userid, submissions=submissions)

    welcome.collection_remove(userid, submissions)
    d.cached_posts_count.invalidate(userid)

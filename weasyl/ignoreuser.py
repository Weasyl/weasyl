from __future__ import absolute_import

from libweasyl import staff

from weasyl import define as d
from weasyl.cache import region
from weasyl.error import WeasylError


def check(userid, otherid):
    """
    check to see if a user is ignored by another
    :param userid: the viewing user
    :param otherid: the user being viewed
    :return: TRUE if userid is ignored by otherid
    """
    if not userid or not otherid:
        return False

    return d.execute("SELECT EXISTS (SELECT 0 FROM ignoreuser WHERE (userid, otherid) = (%i, %i))",
                     [userid, otherid], options="bool")


@region.cache_on_arguments()
@d.record_timing
def cached_list_ignoring(userid):
    return d.execute("SELECT otherid FROM ignoreuser WHERE userid = %i",
                     [userid], options=["within"])


def select(userid, limit, backid=None, nextid=None):
    statement = ["SELECT iu.otherid, pr.username, pr.config FROM ignoreuser iu"
                 " INNER JOIN profile pr ON iu.otherid = pr.userid"
                 " WHERE iu.userid = %i" % (userid,)]

    if backid:
        statement.append(" AND pr.username < (SELECT username FROM profile WHERE userid = %i)" % (backid,))
    elif nextid:
        statement.append(" AND pr.username > (SELECT username FROM profile WHERE userid = %i)" % (nextid,))

    statement.append(" ORDER BY pr.username%s LIMIT %i" % (" DESC" if nextid else "", limit))

    return [{
        "userid": i[0],
        "username": i[1],
    } for i in d.execute("".join(statement))]


def insert(userid, ignore):
    if not ignore:
        return

    with d.engine.begin() as db:
        if isinstance(ignore, list):
            ignore_set = set(ignore)

            if userid in ignore_set:
                raise WeasylError("cannotIgnoreSelf")
            elif ignore_set & staff.MODS:
                raise WeasylError("cannotIgnoreStaff")

            db.execute("""
                INSERT INTO ignoreuser
                SELECT %(user)s, ignore FROM UNNEST (%(ignore)s) AS ignore
                    LEFT JOIN ignoreuser ON ignoreuser.otherid = ignore AND ignoreuser.userid = %(user)s
                    WHERE ignoreuser.otherid IS NULL
            """, user=userid, ignore=ignore)

            db.execute("""
                DELETE FROM frienduser
                WHERE (userid = %(user)s AND otherid = ANY (%(ignore)s))
                    OR (otherid = %(user)s AND userid = ANY (%(ignore)s))
            """, user=userid, ignore=ignore)

            db.execute("""
                DELETE FROM watchuser
                WHERE userid = %(user)s AND otherid = ANY (%(ignore)s)
            """, user=userid, ignore=ignore)
        else:
            if userid == ignore:
                raise WeasylError("cannotIgnoreSelf")
            elif ignore in staff.MODS:
                raise WeasylError("cannotIgnoreStaff")

            db.execute("DELETE FROM frienduser WHERE %(user)s IN (userid, otherid) AND %(ignore)s IN (userid, otherid)",
                       user=userid, ignore=ignore)
            db.execute("DELETE FROM watchuser WHERE userid = %(user)s AND otherid = %(ignore)s",
                       user=userid, ignore=ignore)
            db.execute("INSERT INTO ignoreuser VALUES (%(user)s, %(ignore)s)",
                       user=userid, ignore=ignore)

    cached_list_ignoring.invalidate(userid)

    from weasyl import index
    index.template_fields.invalidate(userid)


def remove(userid, ignore):
    if not ignore:
        return

    if isinstance(ignore, list):
        result = d.engine.execute("DELETE FROM ignoreuser WHERE userid = %(user)s AND otherid = ANY (%(ignore)s)",
                                  user=userid, ignore=ignore)
    else:
        result = d.engine.execute("DELETE FROM ignoreuser WHERE userid = %(user)s AND otherid = %(ignore)s",
                                  user=userid, ignore=ignore)

    if result.rowcount:
        cached_list_ignoring.invalidate(userid)

        from weasyl import index
        index.template_fields.invalidate(userid)

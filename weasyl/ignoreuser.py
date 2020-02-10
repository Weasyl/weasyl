from __future__ import absolute_import

from libweasyl import staff
from libweasyl.cache import region

from weasyl import define as d
from weasyl.error import WeasylError


def check(userid, otherid):
    """
    Return True if otherid is ignored by userid, False otherwise.
    """
    if not userid or not otherid:
        return False

    return d.engine.scalar(
        "SELECT EXISTS (SELECT 0 FROM ignoreuser WHERE (userid, otherid) = (%(user)s, %(other)s))",
        user=userid,
        other=otherid,
    )


@region.cache_on_arguments()
@d.record_timing
def cached_list_ignoring(userid):
    return d.column(d.engine.execute(
        "SELECT otherid FROM ignoreuser WHERE userid = %(user)s",
        user=userid))


def select(userid):
    results = d.engine.execute(
        "SELECT iu.otherid, pr.username FROM ignoreuser iu"
        " INNER JOIN profile pr ON iu.otherid = pr.userid"
        " WHERE iu.userid = %(user)s"
        " ORDER BY lower(pr.username)",
        user=userid
    )

    return [{
        "userid": ignored,
        "username": username,
    } for ignored, username in results]


def insert(userid, ignore):
    if not ignore:
        return

    with d.engine.begin() as db:
        if userid in ignore:
            raise WeasylError("cannotIgnoreSelf")
        elif not staff.MODS.isdisjoint(ignore):
            raise WeasylError("cannotIgnoreStaff")

        db.execute("""
            INSERT INTO ignoreuser
            SELECT %(user)s, ignore FROM UNNEST (%(ignore)s) AS ignore
            ON CONFLICT DO NOTHING
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

    cached_list_ignoring.invalidate(userid)

    from weasyl import index
    index.template_fields.invalidate(userid)


def remove(userid, ignore):
    if not ignore:
        return

    result = d.engine.execute("DELETE FROM ignoreuser WHERE userid = %(user)s AND otherid = ANY (%(ignore)s)",
                              user=userid, ignore=ignore)

    if result.rowcount:
        cached_list_ignoring.invalidate(userid)

        from weasyl import index
        index.template_fields.invalidate(userid)

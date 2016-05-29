# blocktag.py

from error import PostgresError
import define as d

import profile
import searchtag

from libweasyl import ratings

from weasyl.cache import region

# For blocked tags, `rating` refers to the lowest rating for which that tag is
# blocked; for example, (X, Y, 10) would block tag Y for all ratings, whereas
# (X, Y, 30) would block tag Y for only adult ratings.


def check(userid, submitid=None, charid=None, journalid=None):
    """
    Returns True if the submission, character, or journal contains a search tag
    that the user has blocked, else False.
    """
    if not userid:
        return False

    if submitid:
        map_table = "searchmapsubmit"
        content_table = "submission"
        id_field = "submitid"
        target = submitid
    elif charid:
        map_table = "searchmapchar"
        content_table = "character"
        id_field = "charid"
        target = charid
    else:
        map_table = "searchmapjournal"
        content_table = "journal"
        id_field = "journalid"
        target = journalid

    query = """
        SELECT EXISTS (
            SELECT 0 FROM {map_table} searchmap
                INNER JOIN {content_table} content ON searchmap.targetid = content.{id_field}
            WHERE searchmap.targetid = %(id)s
                AND content.userid != %(user)s
                AND searchmap.tagid IN (
                    SELECT blocktag.tagid FROM blocktag
                    WHERE userid = %(user)s AND blocktag.rating <= content.rating)) AS block
    """.format(map_table=map_table, content_table=content_table, id_field=id_field)

    return d.engine.execute(query, id=target, user=userid).first().block


def check_list(rating, tags, blocked_tags):
    return any(rating >= b['rating'] and b['title'] in tags for b in blocked_tags)


def suggest(userid, target):
    if not target:
        return []

    return d.execute("SELECT title FROM searchtag"
                     " WHERE title LIKE '%s%%' AND tagid NOT IN (SELECT tagid FROM blocktag WHERE userid = %i)"
                     " ORDER BY title LIMIT 10", [target, userid], options="within")


def select(userid):
    return [{
        "title": i[0],
        "rating": i[1],
    } for i in d.execute("SELECT st.title, bt.rating FROM searchtag st "
                         " INNER JOIN blocktag bt ON st.tagid = bt.tagid"
                         " WHERE bt.userid = %i"
                         " ORDER BY st.title", [userid])]


@region.cache_on_arguments()
@d.record_timing
def cached_select(userid):
    return select(userid)


def insert(userid, tagid=None, title=None, rating=None):

    if rating not in ratings.CODE_MAP:
        rating = ratings.GENERAL.code

    profile.check_user_rating_allowed(userid, rating)

    if tagid:
        tag = int(tagid)

        try:
            d.engine.execute("INSERT INTO blocktag VALUES (%s, %s, %s)", userid, tag, rating)
        except PostgresError:
            return
    elif title:
        tag_name = d.get_search_tag(title)

        try:
            d.engine.execute("""
                INSERT INTO blocktag (userid, tagid, rating)
                VALUES (
                    %(user)s,
                    (SELECT tagid FROM searchtag WHERE title = %(tag_name)s),
                    %(rating)s
                )
            """, user=userid, tag_name=tag_name, rating=rating)
        except PostgresError:
            try:
                tag = searchtag.create(title)
            except PostgresError:
                return

            d.engine.execute("INSERT INTO blocktag VALUES (%s, %s, %s)", userid, tag, rating)

    cached_select.invalidate(userid)


def remove(userid, tagid=None, title=None):
    if tagid:
        d.execute("DELETE FROM blocktag WHERE (userid, tagid) = (%i, %i)", [userid, tagid])
    elif title:
        d.execute("DELETE FROM blocktag WHERE (userid, tagid) = (%i, (SELECT tagid FROM searchtag WHERE title = '%s'))",
                  [userid, d.get_search_tag(title)])

    cached_select.invalidate(userid)

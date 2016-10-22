from __future__ import absolute_import

import re
import sqlalchemy as sa

from libweasyl import staff

from weasyl import define as d
from weasyl import files
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import orm
from weasyl import welcome
from weasyl.cache import region
from weasyl.error import WeasylError


_TAG_DELIMITER = re.compile(r"[\s,]+")


def select(submitid=None, charid=None, journalid=None):
    return d.execute("SELECT st.title FROM searchtag st"
                     " INNER JOIN searchmap%s sm USING (tagid)"
                     " WHERE sm.targetid = %i"
                     " ORDER BY st.title",
                     [
                         "submit" if submitid else "char" if charid else "journal",
                         submitid if submitid else charid if charid else journalid
                     ], options="within")


def select_with_artist_tags(submitid):
    db = d.connect()
    tags = (
        db.query(orm.Tag.title, orm.SubmissionTag.is_artist_tag)
        .join(orm.SubmissionTag)
        .filter_by(targetid=submitid)
        .order_by(orm.Tag.title)
        .all())
    ret = []
    artist_tags = set()
    for tag, is_artist_tag in tags:
        ret.append(tag)
        if is_artist_tag:
            artist_tags.add(tag)
    return ret, artist_tags


def can_remove_tags(userid, ownerid):
    return userid == ownerid or userid in staff.MODS or 'k' not in d.get_config(ownerid)


def removable_tags(userid, ownerid, tags, artist_tags):
    if not can_remove_tags(userid, ownerid):
        return [tag for tag in tags if tag not in artist_tags]
    else:
        return tags


def select_list(map_table, targetids):
    if not targetids:
        return {}

    mt = map_table
    q = (
        d.sa
        .select([mt.c.targetid, d.sa.func.array_agg(mt.c.tagid)])
        .select_from(mt)
        .where(mt.c.targetid.in_(targetids))
        .group_by(mt.c.targetid))

    db = d.connect()
    return dict(list(db.execute(q)))


@region.cache_on_arguments()
def get_or_create(name):
    name = d.get_search_tag(name)
    tag = d.engine.scalar(
        'INSERT INTO searchtag (title) VALUES (%(name)s) ON CONFLICT (title) DO NOTHING RETURNING tagid',
        name=name)

    if tag is not None:
        return tag

    return d.engine.scalar(
        'SELECT tagid FROM searchtag WHERE title = %(name)s',
        name=name)


def get_ids(names):
    result = d.engine.execute(
        "SELECT tagid, title FROM searchtag WHERE title = ANY (%(names)s)",
        names=list(names))

    return {row.title: row.tagid for row in result}


def tag_array(tagids):
    if not tagids:
        return None
    st = d.meta.tables['searchtag']
    return sa.func.array(
        sa.select([st.c.title])
        .where(st.c.tagid.in_(tagids))
        .as_scalar())


def parse_tags(text):
    tags = set()

    for i in _TAG_DELIMITER.split(text):
        tag = d.get_search_tag(i)

        if tag:
            tags.add(tag)

    return tags


def parse_blacklist_tags(text, get_first_element=False):
    """
    A custom implementation of ``parse_tags()`` for the searchtag blacklist.
    Enforces the desired characteristics of STBL tags, and allows an asterisk
       character, whereas ``parse_tags()`` would strip asterisks.

    Parameters:
        text: The string to parse for tags
        get_first_element: Defaults to Boolean False. Returns only the first element of the tags set().

    Returns:
        tags: A set() with valid tags.
        element: The first element in the tags set(), if get_first_element is True.
    """
    tags = set()

    for i in _TAG_DELIMITER.split(text):
        target = "".join([c for c in i if ord(c) < 128])
        target = target.replace(" ", "_")
        target = "".join(i for i in target if i.isalnum() or i in "_*")
        target = target.strip("_")
        target = "_".join(i for i in target.split("_") if i)

        if target.count("*") < 2 and "*" in target and len(target) > 2:
            tags.add(target)
        elif not target.count("*") and len(target):
            tags.add(target)

    if get_first_element:
        for element in tags:
            return element
    return tags


def associate(userid, tags, submitid=None, charid=None, journalid=None):
    targetid = d.get_targetid(submitid, charid, journalid)

    # Assign table, feature, ownerid
    if submitid:
        table, feature = "searchmapsubmit", "submit"
        ownerid = d.get_ownerid(submitid=targetid)
    elif charid:
        table, feature = "searchmapchar", "char"
        ownerid = d.get_ownerid(charid=targetid)
    else:
        table, feature = "searchmapjournal", "journal"
        ownerid = d.get_ownerid(journalid=targetid)

    # Check permissions and invalid target
    if not ownerid:
        raise WeasylError("TargetRecordMissing")
    elif userid != ownerid and "g" in d.get_config(userid):
        raise WeasylError("InsufficientPermissions")
    elif ignoreuser.check(ownerid, userid):
        raise WeasylError("contentOwnerIgnoredYou")

    # Determine previous tags
    existing = d.engine.execute(
        "SELECT tagid, settings FROM {} WHERE targetid = %(target)s".format(table),
        target=targetid).fetchall()

    # Determine tag titles and tagids
    query = d.engine.execute(
        "SELECT tagid, title FROM searchtag WHERE title = ANY (%(tags)s)",
        tags=list(tags)).fetchall()

    newtags = list(tags - {x.title for x in query})

    if newtags:
        query.extend(
            d.engine.execute(
                "INSERT INTO searchtag (title) SELECT * FROM UNNEST (%(newtags)s) AS title RETURNING tagid, title",
                newtags=newtags
            ).fetchall())

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    # Check removed artist tags
    if not can_remove_tags(userid, ownerid):
        existing_artist_tags = {t.tagid for t in existing if 'a' in t.settings}
        removed.difference_update(existing_artist_tags)
        entered_tagids.update(existing_artist_tags)

    # If the modifying user is not the owner of the object, check user/global blacklists
    if userid != ownerid:
        # Get the blacklisted tags
        blacklisted_tags = query_blacklisted_tags(added, ownerid)
        # Remove tags that are blacklisted (if any)
        added -= blacklisted_tags

    # Remove tags
    if removed:
        d.engine.execute(
            "DELETE FROM {} WHERE targetid = %(target)s AND tagid = ANY (%(removed)s)".format(table),
            target=targetid, removed=list(removed))

    if added:
        d.engine.execute(
            "INSERT INTO {} SELECT tag, %(target)s FROM UNNEST (%(added)s) AS tag".format(table),
            target=targetid, added=list(added))

        if userid == ownerid:
            d.execute(
                "UPDATE %s SET settings = settings || 'a' WHERE targetid = %i AND tagid IN %s",
                [table, targetid, d.sql_number_list(list(added))])

    if submitid:
        d.engine.execute(
            'INSERT INTO submission_tags (submitid, tags) VALUES (%(submission)s, %(tags)s) '
            'ON CONFLICT (submitid) DO UPDATE SET tags = %(tags)s',
            submission=submitid, tags=list(entered_tagids))

        db = d.connect()
        db.execute(
            d.meta.tables['tag_updates'].insert()
            .values(submitid=submitid, userid=userid,
                    added=tag_array(added), removed=tag_array(removed)))
        if userid != ownerid:
            welcome.tag_update_insert(ownerid, submitid)

    files.append(
        "%stag.%s.%s.log" % (m.MACRO_SYS_LOG_PATH, feature, d.get_timestamp()),
        "-%sID %i  -T %i  -UID %i  -X %s\n" % (feature[0].upper(), targetid, d.get_time(), userid,
                                               " ".join(tags)))


def tag_history(submitid):
    db = d.connect()
    tu = d.meta.tables['tag_updates']
    pr = d.meta.tables['profile']
    return db.execute(
        sa.select([pr.c.username, tu.c.updated_at, tu.c.added, tu.c.removed])
        .select_from(tu.join(pr, tu.c.userid == pr.c.userid))
        .where(tu.c.submitid == submitid)
        .order_by(tu.c.updated_at.desc()))


def edit_searchtag_blacklist(userid, tags, edit_global_blacklist=False):
    """
    Manages the user or global searchtag blacklists, adding or removing
    tags as appropriate

    Parameters:
        userid: The userid of the user submitting the request.
        tags: A set() object of tags.
        edit_global_blacklist: Optional. Set to Boolean True if the global blacklist is to be edited.

    Returns:
        Nothing.
    """
    # Only directors can edit the global blacklist; sanity check against the @director_only decorator
    if edit_global_blacklist and userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    # Determine what, if any, tags exist before editing, depending on what we are editing
    if not edit_global_blacklist:
        existing = d.engine.execute("""
            SELECT tagid FROM searchmapuserblacklist WHERE userid = %(uid)s
        """, uid=userid).fetchall()
    else:
        existing = d.engine.execute("""
            SELECT tagid FROM searchmapglobalblacklist
        """).fetchall()

    # Get the tag titles/ids out of the searchtag table
    query = d.engine.execute("""
        SELECT tagid, title FROM searchtag WHERE title = ANY (%(title)s)
    """, title=list(tags)).fetchall()

    # Determine if the tag is 'valid' for the blacklist by consulting ``parse_blacklist_tags()``
    tags = {parse_blacklist_tags(tag, get_first_element=True) for tag in tags if parse_blacklist_tags(tag, get_first_element=True)}

    # Determine which (if any) of the valid tags are new; add them to the searchtag table if so.
    newtags = list(tags - {x.title for x in query})
    if newtags:
        query.extend(
            d.engine.execute(
                "INSERT INTO searchtag (title) SELECT * FROM UNNEST (%(newtags)s) AS title RETURNING tagid, title",
                newtags=newtags
            ).fetchall())

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    if added:
        if edit_global_blacklist:
            d.engine.execute("""
                INSERT INTO searchmapglobalblacklist
                    SELECT tag, %(uid)s
                    FROM UNNEST (%(added)s) AS tag
            """, uid=userid, added=list(added))
        else:
            d.engine.execute("""
                INSERT INTO searchmapuserblacklist
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
            """, uid=userid, added=list(added))

    if removed:
        if edit_global_blacklist:
            d.engine.execute("""
                DELETE FROM searchmapglobalblacklist
                WHERE tagid = ANY (%(removed)s)
            """, removed=list(removed))
        else:
            d.engine.execute("""
                DELETE FROM searchmapuserblacklist
                WHERE userid = %(uid)s AND tagid = ANY (%(removed)s)
            """, uid=userid, removed=list(removed))


def get_searchtag_blacklist(userid, global_blacklist=False):
    """
    Retrieves a list of tags on the (user|global)blacklist for friendly display to the user.

    Parameters:
        userid: The userid of the user requesting the list of tags.
        global_blacklist: Boolean True if requesting tags from the global blacklist. Defaults to False.

    Returns:
        A list of searchtags (and users for global blacklist requests).
    """
    # Only directors can edit the global blacklist; sanity check against the @director_only decorator
    if global_blacklist and userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    # Tags on the global blacklist are being requested
    if global_blacklist:
        query = d.engine.execute("""
            SELECT st.title, lo.login_name
            FROM searchmapglobalblacklist
            INNER JOIN searchtag AS st USING (tagid)
            INNER JOIN login AS lo USING (userid)
            ORDER BY st.title ASC
        """).fetchall()
        return query
    # User blacklist tags are being requested
    else:
        query = d.engine.execute("""
            SELECT st.title
            FROM searchmapuserblacklist
            INNER JOIN searchtag AS st USING (tagid)
            WHERE userid = %(userid)s
            ORDER BY st.title ASC
        """, userid=userid).fetchall()
        tags = [tag.title for tag in query]
        return tags


def query_blacklisted_tags(newtagids, ownerid):
    """
    Checks both the user and global searchtag blacklists against added tags, and
        returns the IDs of any tags matching the STBL, either based on strict
        match, or regexp based match.

    Parameters:
        newtagids: The list of added tag ids.
        ownerid: The userid of the submitted item being checked.

    Returns:
        blacklisted_tags: The tagids which are blacklisted as a set()
    """
    blacklist_query = d.engine.execute("""
        SELECT st.tagid, st.title
        FROM searchmapuserblacklist
        INNER JOIN searchtag AS st USING (tagid)
        WHERE userid = %(ownerid)s
        UNION
        SELECT st.tagid, st.title
        FROM searchmapglobalblacklist
        INNER JOIN searchtag AS st USING (tagid)
    """, ownerid=ownerid).fetchall()
    tag_titles = d.engine.execute("""
        SELECT title, tagid
        FROM searchtag
        WHERE tagid = ANY (%(tagids)s)
    """, tagids=list(newtagids)).fetchall()

    blacklisted_tag_ids = set()

    for x in blacklist_query:
        # Determine if the candidate ID is directly present in the newly added IDs.
        if x.tagid in newtagids:
            blacklisted_tag_ids.add(x.tagid)
        # Otherwise we need to parse for wildcards
        elif x.title.count("*"):
            # Convert '*' to '.*' as expected by regexp.
            regex = x.title.replace("*", ".*")
            for i in tag_titles:
                if re.match(regex, i.title):
                    blacklisted_tag_ids.add(i.tagid)

    return blacklisted_tag_ids

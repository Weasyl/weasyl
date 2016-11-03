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


def parse_restricted_tags(text):
    """
    A custom implementation of ``parse_tags()`` for the searchtag restriction list.
    Enforces the desired characteristics of STBL tags, and allows an asterisk
    character, whereas ``parse_tags()`` would strip asterisks.

    Parameters:
        text: The string to parse for tags

    Returns:
        tags: A set() with valid tags.
    """
    tags = set()

    for i in _TAG_DELIMITER.split(text):
        target = "".join([c for c in i if ord(c) < 128])
        target = "".join(i for i in target if i.isalnum() or i in "_*")
        target = target.strip("_")
        target = "_".join(i for i in target.split("_") if i)

        if is_searchtag_restriction_pattern_valid(target):
            tags.add(target.lower())

    return tags


def is_searchtag_restriction_pattern_valid(text):
    """
    Determines if a given piece of text is considered a valid searchtag restriction pattern.

    Parameters:
        text: A candidate searchtag restriction entry

    Returns:
        Boolean True if the tag is considered to be a valid pattern. Boolean False otherwise.
    """
    if text.count("*") == 1 and len(text) > 2:
        return True
    elif text and "*" not in text:
        return True
    return False


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

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    query = add_and_get_searchtags(tags)

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    # If the modifying user is not the owner of the object, and is not staff, check user/global restriction lists
    if userid != ownerid and userid not in staff.MODS:
        stbl_tags = query_user_restricted_tags(ownerid) + query_global_restricted_tags()
        added -= remove_restricted_tags(stbl_tags, query)

    # Check removed artist tags
    if not can_remove_tags(userid, ownerid):
        existing_artist_tags = {t.tagid for t in existing if 'a' in t.settings}
        removed.difference_update(existing_artist_tags)
        entered_tagids.update(existing_artist_tags)

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


def add_and_get_searchtags(tags):
    """
    Handles addition of, and getting existing, searchtags, abstracting the logic
    for addition of such from editing functions. Serves to consolidate otherwise
    duplicated code.

    Parameters:
        tags: A set of tags.

    Returns:
        query: The results of a SQL query which contains tagids and titles for
        tags which either currently exist, or were added as a result
        of this function.
    """
    # Get the tag titles/ids out of the searchtag table
    query = d.engine.execute("""
        SELECT tagid, title FROM searchtag WHERE title = ANY (%(title)s)
    """, title=list(tags)).fetchall()

    # Determine which (if any) of the valid tags are new; add them to the searchtag table if so.
    newtags = list(tags - {x.title for x in query})
    if newtags:
        query.extend(
            d.engine.execute(
                "INSERT INTO searchtag (title) SELECT * FROM UNNEST (%(newtags)s) AS title RETURNING tagid, title",
                newtags=newtags
            ).fetchall())
    return query


def edit_user_searchtag_restrictions(userid, tags):
    """
    Edits the user searchtag restriction list, by dropping all rows for ``userid`` and reinserting
    any ``tags`` passed in to the function.

    Parameters:
        userid: The userid of the user submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/settings.py controller)

    Returns:
        Nothing.
    """
    # First, drop all rows from the searchmapuserrestrictedtags table for userid
    d.engine.execute("""
        DELETE FROM searchmapuserrestrictedtags
        WHERE userid = %(uid)s
    """, uid=userid)

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    query = add_and_get_searchtags(tags)

    # Insert the new STBL user entries into the table (if we have any tags to add)
    if query:
        d.engine.execute("""
            INSERT INTO searchmapuserrestrictedtags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=[tag.tagid for tag in query])

    # Clear the user STBL cache, since we made changes
    query_user_restricted_tags.invalidate(userid)


def edit_global_searchtag_restrictions(userid, tags):
    """
    Edits the global searchtag restriction list, adding or removing tags as appropriate.

    Parameters:
        userid: The userid of the director submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/director.py controller)

    Returns:
        Nothing.
    """
    # Only directors can edit the global restriction list; sanity check against the @director_only decorator
    if userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    existing = d.engine.execute("""
        SELECT tagid FROM searchmapglobalrestrictedtags
    """).fetchall()

    # Retrieve tag titles and tagid pairs, for new and existing tags
    query = add_and_get_searchtags(tags)

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    if added:
        d.engine.execute("""
            INSERT INTO searchmapglobalrestrictedtags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=list(added))

    if removed:
        d.engine.execute("""
            DELETE FROM searchmapglobalrestrictedtags
            WHERE tagid = ANY (%(removed)s)
        """, removed=list(removed))

    # Clear the global STBL cache if any changes were made
    if added or removed:
        query_global_restricted_tags.invalidate()


def get_user_searchtag_restrictions(userid):
    """
    Retrieves a list of tags on the user searchtag restriction list for friendly display to the user.

    Parameters:
        userid: The userid of the user requesting the list of tags.

    Returns:
        A list of restricted searchtag titles which were set by ``userid``.
    """
    query = d.engine.execute("""
        SELECT st.title
        FROM searchmapuserrestrictedtags
        INNER JOIN searchtag AS st USING (tagid)
        WHERE userid = %(userid)s
        ORDER BY st.title
    """, userid=userid).fetchall()
    tags = [tag.title for tag in query]
    return tags


def get_global_searchtag_restrictions(userid):
    """
    Retrieves a list of tags on the global searchtag restriction list for friendly display to the director.

    Parameters:
        userid: The userid of the director requesting the list of tags.

    Returns:
        A list of globally restricted searchtag titles and the name of the director which added it.
    """
    # Only directors can view the global searchtag restriction list; sanity check against the @director_only decorator
    if userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    return d.engine.execute("""
        SELECT st.title, lo.login_name
        FROM searchmapglobalrestrictedtags
        INNER JOIN searchtag AS st USING (tagid)
        INNER JOIN login AS lo USING (userid)
        ORDER BY st.title
    """).fetchall()


@region.cache_on_arguments()
def query_user_restricted_tags(ownerid):
    """
    Gets and returns restricted searchtag tags for users.

    Parameters:
        ownerid: The userid of the user who owns the content tags are being added to.

    Returns:
        A list of user STBL tag titles.
    """
    query = d.engine.execute("""
        SELECT title
        FROM searchmapuserrestrictedtags
        INNER JOIN searchtag USING (tagid)
        WHERE userid = %(ownerid)s
    """, ownerid=ownerid).fetchall()
    return [tag.title for tag in query]


@region.cache_on_arguments()
def query_global_restricted_tags():
    """
    Gets and returns globally restricted searchtag tags.

    Parameters:
        None. Retrieves all global searchtag restriction entries.

    Returns:
        A list of global STBL tag titles
    """
    query = d.engine.execute("""
        SELECT title
        FROM searchmapglobalrestrictedtags
        INNER JOIN searchtag USING (tagid)
    """).fetchall()
    return [tag.title for tag in query]


def remove_restricted_tags(patterns, tags):
    """
    Determines what, if any, new search tags match tags that are on the user/global
      searchtag blocklist.

    Parameters:
        patterns: The result of ``query_user_restricted_tags(ownerid) +
        query_global_restricted_tags()``. Consists
        of a list of titles of patterns which match a restricted tag.

        tags: The reused SQL query result from ``associate()`` which consists of tagids
        and titles for tags passed to the function.

    Returns:
        A set() of tagids which have been restricted.
    """
    regex = r"(?:%s)\Z" % ("|".join(pattern.replace("*", ".*") for pattern in patterns),)
    return {tag.tagid for tag in tags if re.match(regex, tag.title)}

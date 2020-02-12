from __future__ import absolute_import

import re
import sqlalchemy as sa

from libweasyl import staff
from libweasyl.cache import region

from weasyl import define as d
from weasyl import files
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import welcome
from weasyl.error import WeasylError


_TAG_DELIMITER = re.compile(r"[\s,]+")
# limited so people can't give themselves every tag
# and hog the top of marketplace results
MAX_PREFERRED_TAGS = 50


def select(submitid=None, charid=None, journalid=None):
    return d.column(d.engine.execute(
        "SELECT st.title FROM searchtag st"
        " INNER JOIN searchmap{suffix} sm USING (tagid)"
        " WHERE sm.targetid = %(target)s"
        " ORDER BY st.title".format(
            suffix="submit" if submitid else "char" if charid else "journal",
        ),
        target=submitid if submitid else charid if charid else journalid,
    ))


def select_with_artist_tags(submitid):
    # 'a': artist-tag
    tags = d.engine.execute(
        "SELECT title, settings ~ 'a'"
        " FROM searchmapsubmit"
        " INNER JOIN searchtag USING (tagid)"
        " WHERE targetid = %(sub)s"
        " ORDER BY title",
        sub=submitid,
    ).fetchall()

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
    A custom implementation of ``parse_tags()`` for the restricted tag list.
    Enforces the desired characteristics of restricted tags, and allows an asterisk
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

        if is_tag_restriction_pattern_valid(target):
            tags.add(target.lower())

    return tags


def is_tag_restriction_pattern_valid(text):
    """
    Determines if a given piece of text is considered a valid restricted tag pattern.

    Valid patterns:
    - Length: 0 < x <= 100 -- Prevents absurd tag lengths.
    - If string contains a ``*``, must only contain one *, and be three characters or more.

    Parameters:
        text: A single candidate restricted tag entry.

    Returns:
        Boolean True if the tag is considered to be a valid pattern. Boolean False otherwise.
    """
    if len(text) > 100:
        return False
    elif text.count("*") == 1 and len(text) > 2:
        return True
    elif text and "*" not in text:
        return True
    return False


def associate(userid, tags, submitid=None, charid=None, journalid=None, preferred_tags_userid=None, optout_tags_userid=None):
    """
    Associates searchtags with a content item.

    Parameters:
        userid: The userid of the user associating tags
        tags: A set of tags
        submitid: The ID number of a submission content item to associate
        ``tags`` to. (default: None)
        charid: The ID number of a character content item to associate
        ``tags`` to. (default: None)
        journalid: The ID number of a journal content item to associate
        ``tags`` to. (default: None)
        preferred_tags_userid: The ID number of a user to associate
        ``tags`` to for Preferred tags. (default: None)
        optout_tags_userid: The ID number of a user to associate
        ``tags`` to for Opt-Out tags. (default: None)

    Returns:
        A dict containing two elements. 1) ``add_failure_restricted_tags``, which contains a space separated
        string of tag titles which failed to be added to the content item due to the user or global restricted
        tag lists; and 2) ``remove_failure_owner_set_tags``, which contains a space separated string of tag
        titles which failed to be removed from the content item due to the owner of the aforementioned item
        prohibiting users from removing tags set by the content owner.

        If an element does not have tags, the element is set to None. If neither elements are set,
        the function returns None.
    """
    targetid = d.get_targetid(submitid, charid, journalid)

    # Assign table, feature, ownerid
    if submitid:
        table, feature = "searchmapsubmit", "submit"
        ownerid = d.get_ownerid(submitid=targetid)
    elif charid:
        table, feature = "searchmapchar", "char"
        ownerid = d.get_ownerid(charid=targetid)
    elif journalid:
        table, feature = "searchmapjournal", "journal"
        ownerid = d.get_ownerid(journalid=targetid)
    elif preferred_tags_userid:
        table, feature = "artist_preferred_tags", "user"
        targetid = ownerid = preferred_tags_userid
    elif optout_tags_userid:
        table, feature = "artist_optout_tags", "user"
        targetid = ownerid = optout_tags_userid
    else:
        raise WeasylError("Unexpected")

    # Check permissions and invalid target
    if not ownerid:
        raise WeasylError("TargetRecordMissing")
    elif userid != ownerid and ("g" in d.get_config(userid) or preferred_tags_userid or optout_tags_userid):
        # disallow if user is forbidden from tagging, or trying to set artist tags on someone other than themselves
        raise WeasylError("InsufficientPermissions")
    elif ignoreuser.check(ownerid, userid):
        raise WeasylError("contentOwnerIgnoredYou")

    # Determine previous tagids, titles, and settings
    existing = d.engine.execute(
        "SELECT tagid, title, settings FROM {} INNER JOIN searchtag USING (tagid) WHERE targetid = %(target)s".format(table),
        target=targetid).fetchall()

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    query = add_and_get_searchtags(tags)

    existing_tagids = {t.tagid for t in existing}
    entered_tagids = {t.tagid for t in query}

    # Assign added and removed
    added = entered_tagids - existing_tagids
    removed = existing_tagids - entered_tagids

    # enforce the limit on artist preference tags
    if preferred_tags_userid and (len(added) - len(removed) + len(existing)) > MAX_PREFERRED_TAGS:
        raise WeasylError("tooManyPreferenceTags")

    # Track which tags fail to be added or removed to later notify the user (Note: These are tagids at this stage)
    add_failure_restricted_tags = None
    remove_failure_owner_set_tags = None

    # If the modifying user is not the owner of the object, and is not staff, check user/global restriction lists
    if userid != ownerid and userid not in staff.MODS:
        user_rtags = set(query_user_restricted_tags(ownerid))
        global_rtags = set(query_global_restricted_tags())
        add_failure_restricted_tags = remove_restricted_tags(user_rtags | global_rtags, query)
        added -= add_failure_restricted_tags
        if len(add_failure_restricted_tags) == 0:
            add_failure_restricted_tags = None

    # Check removed artist tags
    if not can_remove_tags(userid, ownerid):
        existing_artist_tags = {t.tagid for t in existing if 'a' in t.settings}
        remove_failure_owner_set_tags = removed & existing_artist_tags
        removed.difference_update(existing_artist_tags)
        entered_tagids.update(existing_artist_tags)
        # Submission items use a different method of tag protection for artist tags; ignore them
        if submitid or len(remove_failure_owner_set_tags) == 0:
            remove_failure_owner_set_tags = None

    # Remove tags
    if removed:
        d.engine.execute(
            "DELETE FROM {} WHERE targetid = %(target)s AND tagid = ANY (%(removed)s)".format(table),
            target=targetid, removed=list(removed))

    if added:
        d.engine.execute(
            "INSERT INTO {} SELECT tag, %(target)s FROM UNNEST (%(added)s) AS tag".format(table),
            target=targetid, added=list(added))

        # preference/optout tags can only be set by the artist, so this settings column does not apply
        if userid == ownerid and not (preferred_tags_userid or optout_tags_userid):
            d.engine.execute(
                "UPDATE {} SET settings = settings || 'a' WHERE targetid = %(target)s AND tagid = ANY (%(added)s)".format(table),
                target=targetid, added=list(added))

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

    # Return dict with any tag titles as a string that failed to be added or removed
    if add_failure_restricted_tags or remove_failure_owner_set_tags:
        if add_failure_restricted_tags:
            add_failure_restricted_tags = " ".join({tag.title for tag in query if tag.tagid in add_failure_restricted_tags})
        if remove_failure_owner_set_tags:
            remove_failure_owner_set_tags = " ".join({tag.title for tag in existing if tag.tagid in remove_failure_owner_set_tags})
        return {"add_failure_restricted_tags": add_failure_restricted_tags,
                "remove_failure_owner_set_tags": remove_failure_owner_set_tags}
    else:
        return None


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
    Handles addition of--and getting existing--searchtags, abstracting the logic
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


def edit_user_tag_restrictions(userid, tags):
    """
    Edits the user's restricted tag list, by dropping all rows for ``userid`` and reinserting
    any ``tags`` passed in to the function.

    Parameters:
        userid: The userid of the user submitting the request.

        tags: A set() object of tags; must have been passed through ``parse_restricted_tags()``
        (occurs in the the controllers/settings.py controller)

    Returns:
        Nothing.
    """
    # First, drop all rows from the user_restricted_tags table for userid
    d.engine.execute("""
        DELETE FROM user_restricted_tags
        WHERE userid = %(uid)s
    """, uid=userid)

    # Retrieve tag titles and tagid pairs, for new (if any) and existing tags
    query = add_and_get_searchtags(tags)

    # Insert the new restricted tag for ``userid`` entries into the table (if we have any tags to add)
    if query:
        d.engine.execute("""
            INSERT INTO user_restricted_tags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=[tag.tagid for tag in query])

    # Clear the cache for ``userid``'s restricted tags, since we made changes
    query_user_restricted_tags.invalidate(userid)


def edit_global_tag_restrictions(userid, tags):
    """
    Edits the globally restricted tag list, adding or removing tags as appropriate.

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
        SELECT tagid FROM globally_restricted_tags
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
            INSERT INTO globally_restricted_tags (tagid, userid)
                SELECT tag, %(uid)s
                FROM UNNEST (%(added)s) AS tag
        """, uid=userid, added=list(added))

    if removed:
        d.engine.execute("""
            DELETE FROM globally_restricted_tags
            WHERE tagid = ANY (%(removed)s)
        """, removed=list(removed))

    # Clear the globally restricted tags cache if any changes were made
    if added or removed:
        query_global_restricted_tags.invalidate()


def get_global_tag_restrictions(userid):
    """
    Retrieves a list of tags on the globally restricted tag list for display to a director.

    Parameters:
        userid: The userid of the director requesting the list of tags.

    Returns:
        A dict mapping from globally restricted tag titles to the name of the director who added the tag.
    """
    # Only directors can view the globally restricted tag list; sanity check against the @director_only decorator
    if userid not in staff.DIRECTORS:
        raise WeasylError("InsufficientPermissions")

    query = d.engine.execute("""
        SELECT st.title, lo.login_name
        FROM globally_restricted_tags
        INNER JOIN searchtag AS st USING (tagid)
        INNER JOIN login AS lo USING (userid)
    """).fetchall()
    return {r.title: r.login_name for r in query}


@region.cache_on_arguments()
def query_user_restricted_tags(ownerid):
    """
    Gets and returns restricted tags for users.

    Parameters:
        ownerid: The userid of the user who owns the content tags are being added to.

    Returns:
        A list of user restricted tag titles, in no particular order.
    """
    query = d.engine.execute("""
        SELECT title
        FROM user_restricted_tags
        INNER JOIN searchtag USING (tagid)
        WHERE userid = %(ownerid)s
    """, ownerid=ownerid).fetchall()
    return [tag.title for tag in query]


@region.cache_on_arguments()
def query_global_restricted_tags():
    """
    Gets and returns globally restricted tags.

    Parameters:
        None. Retrieves all global tag restriction entries.

    Returns:
        A list of global restricted tag titles, in no particular order.
    """
    query = d.engine.execute("""
        SELECT title
        FROM globally_restricted_tags
        INNER JOIN searchtag USING (tagid)
    """).fetchall()
    return [tag.title for tag in query]


def remove_restricted_tags(patterns, tags):
    """
    Determines what, if any, new search tags match tags that are on the user or global
      restricted tag list.

    Parameters:
        patterns: The result of ``query_user_restricted_tags(ownerid) +
        query_global_restricted_tags()``. Consists
        of a list of titles of patterns which match a restricted tag.

        tags: The reused SQL query result from ``associate()`` which consists of tagids
        and titles for tags passed to the function.

    Returns:
        A set of tagids which have been restricted.
    """
    regex = r"(?:%s)\Z" % ("|".join(pattern.replace("*", ".*") for pattern in patterns),)
    return {tag.tagid for tag in tags if re.match(regex, tag.title)}

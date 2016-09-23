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

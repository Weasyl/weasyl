from __future__ import absolute_import

import sqlalchemy as sa

from weasyl import define as d
from weasyl import media
from weasyl.error import WeasylError


_TITLE = 100


def check(userid, folderid=None, title=None, parentid=None, root=True):
    """
    Returns True if folderid or title refers to a non-hidden folder owned by
    the user, else False. Additionally, if parentid is non-None, it must refer
    to the parent folder.
    """
    if not folderid and not title:
        return root

    if folderid:
        if parentid is None:
            return d.engine.scalar(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (folderid, userid) = (%(folder)s, %(user)s) AND settings !~ 'h')",
                folder=folderid, user=userid)
        else:
            return d.engine.scalar(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (folderid, userid, parentid) = (%(folder)s, %(user)s, %(parent)s) AND settings !~ 'h')",
                folder=folderid, user=userid, parent=parentid)
    elif title:
        if parentid is None:
            return d.engine.scalar(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (userid, title) = (%(user)s, %(title)s) AND settings !~ 'h')",
                user=userid, title=title)
        else:
            return d.engine.scalar(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (userid, parentid, title) = (%(user)s, %(parent)s, %(title)s) AND settings !~ 'h')",
                user=userid, parent=parentid, title=title)


def create(userid, title, parentid):
    title = title.strip()[:_TITLE]
    parentid = d.get_int(parentid)

    if not check(userid, parentid, parentid=0, root=True):
        raise WeasylError("folderRecordMissing")
    elif not title.strip():
        raise WeasylError("titleInvalid")
    elif check(userid, title=title, parentid=parentid):
        raise WeasylError("folderRecordExists")

    d.engine.execute(
        "INSERT INTO folder (parentid, userid, title)"
        " VALUES (%(parent)s, %(user)s, %(title)s)",
        parent=parentid,
        user=userid,
        title=title,
    )


def select_info(folderid):
    db = d.connect()
    f = d.meta.tables['folder']
    q = sa.select([f.c.title, f.c.settings]).where(f.c.folderid == folderid)
    results = db.execute(q).fetchall()
    return results[0]


def update_settings(folderid, settings):
    f = d.meta.tables['folder']
    q = f.update().where(f.c.folderid == folderid).values(settings=''.join({'f', 'm', 'u', 'n'} & set(settings)))
    d.engine.execute(q)


def submission_has_folder_flag(submitid, flag):
    f = d.meta.tables['folder']
    su = d.meta.tables['submission']
    q = (sa.select([f.c.settings.op('~')(flag)])
         .select_from(f.outerjoin(su, f.c.folderid == su.c.folderid))
         .where(su.c.submitid == submitid))
    results = d.engine.execute(q).fetchall()
    return bool(results and results[0][0])


def select_preview(userid, otherid, rating, limit=3):
    """
    Picks out random folders up to the limit, and get a count, name, and random
    submission to use as a preview for each.

    The rules below ensure that the following images won't be used or counted:
    Hidden images, friends only images from non-friends, submissions above the
    specified rating. Except for hidden images, these rules are ignored when
    a user views their own folders.

    Params:
        userid: The id of the viewing user.
        otherid: The id of the users whose folders we're viewing.
        rating: The maximum rating of submissions that will be considered for
            counts or a preview.
        limit: The maximum number of folders to consider. Defaults to 3.

    Returns:
        An array of dicts, each of which has a folderid, a title, a count, and
        sub_media to use for a preview.
    """
    query = []
    folder_query = d.engine.execute("""
        SELECT
            fd.folderid, fd.title,
            (SELECT COUNT(*)
               FROM submission su
               WHERE folderid = fd.folderid
                 AND settings !~ '[hu]'
                 AND (rating <= %(rating)s OR (userid = %(userid)s AND NOT %(sfwmode)s))
                 AND (settings !~ 'f'
                      OR su.userid = %(userid)s
                      OR EXISTS (SELECT 0
                                   FROM frienduser
                                   WHERE ((userid, otherid) = (%(userid)s, su.userid)
                                          OR (userid, otherid) = (su.userid, %(userid)s))
                                     AND settings !~ 'p')))
        FROM folder fd
        WHERE fd.userid = %(otherid)s
            AND fd.settings !~ '[hu]'
            AND EXISTS (SELECT 0 FROM submission
                          WHERE folderid = fd.folderid
                            AND (rating <= %(rating)s OR (userid = %(userid)s AND NOT %(sfwmode)s)))
        ORDER BY RANDOM()
        LIMIT %(limit)s
    """, rating=rating, userid=userid, otherid=otherid, limit=limit, sfwmode=d.is_sfw_mode())

    for i in folder_query:
        submit = d.engine.execute("""
            SELECT submitid, settings FROM submission su
                WHERE (rating <= %(rating)s OR (userid = %(userid)s AND NOT %(sfwmode)s))
                AND folderid = %(folderid)s AND settings !~ 'h'
                AND (settings !~ 'f' OR su.userid = %(userid)s
                     OR EXISTS (SELECT 0 FROM frienduser
                                  WHERE ((userid, otherid) = (%(userid)s, su.userid)
                                         OR (userid, otherid) = (su.userid, %(userid)s))
                                    AND settings !~ 'p'))
                ORDER BY RANDOM() LIMIT 1
            """, rating=rating, folderid=i.folderid, userid=userid, sfwmode=d.is_sfw_mode()).first()

        if submit:
            query.append({
                "folderid": i.folderid,
                "title": i.title,
                "count": i.count,
                "userid": otherid,
                "sub_media": media.get_submission_media(submit.submitid),
            })

    return query


def select_list(userid, feature):
    result = []

    # Select for sidebar
    if feature == "sidebar/all":
        query = d.execute("""
            SELECT
                fd.folderid, fd.title, fd.parentid
            FROM folder fd
            WHERE fd.userid = %i
                AND fd.settings !~ 'h'
            ORDER BY fd.parentid, fd.title
        """, [userid])

        for i in range(len(query)):
            if query[i][2]:
                break

            result.append({
                "folderid": query[i][0],
                "title": query[i][1],
                "subfolder": False,
            })

            for j in range(i + 1, len(query)):
                if query[j][2] == query[i][0]:
                    result.append({
                        "folderid": query[j][0],
                        "title": query[j][1],
                        "subfolder": True,
                    })
    # Select for dropdown
    else:
        query = d.execute(
            "SELECT folderid, title, parentid FROM folder WHERE userid = %i AND settings !~ 'h' ORDER BY parentid, title",
            [userid])

        for i in range(len(query)):
            if query[i][2]:
                break

            result.append({
                "folderid": query[i][0],
                "title": query[i][1],
                "subfolder": False,
                "haschildren": False,
            })

            if feature == "drop/all" or feature == "api/all":
                has_children = set()

                for j in range(i + 1, len(query)):
                    if query[j][2] == query[i][0]:
                        if feature == "drop/all":
                            title = "%s / %s" % (query[i][1], query[j][1])
                        else:
                            title = query[j][1]

                        result.append({
                            "folderid": query[j][0],
                            "title": title,
                            "subfolder": True,
                            "parentid": query[j][2],
                            "haschildren": False
                        })

                        if not query[j][2] in has_children:
                            has_children.add(query[j][2])

                for m in (f for f in result if f["folderid"] in has_children):
                    m["haschildren"] = True

    return result


def rename(userid, title, folderid):
    title = title.strip()[:_TITLE]
    folderid = d.get_int(folderid)

    query = d.engine.scalar("SELECT userid FROM folder WHERE folderid = %(folder)s",
                            folder=folderid)

    if not query:
        raise WeasylError("folderRecordMissing")
    elif not title:
        raise WeasylError("titleInvalid")
    elif userid != query:
        raise WeasylError("InsufficientPermissions")

    d.engine.execute(
        "UPDATE folder SET title = %(title)s WHERE folderid = %(folder)s",
        title=title, folder=folderid)


def move(userid, folderid, parentid):
    folderid = d.get_int(folderid)
    parentid = d.get_int(parentid)

    folder_query = d.execute(
        "SELECT folderid, parentid, userid, title FROM folder WHERE folderid = %i",
        [folderid])

    if not folder_query:
        raise WeasylError("folderRecordMissing")
    # folder cannot be a subfolder of itself
    elif folderid == parentid:
        raise WeasylError("parentidInvalid")
    # folder cannot be a subfolder of another user's folder
    elif userid != folder_query[0][2]:
        raise WeasylError("InsufficientPermissions")
    # folder with subfolders cannot become a subfolder
    elif (folderid and
          d.engine.scalar("SELECT EXISTS (SELECT 0 FROM folder WHERE parentid = %(parent)s)",
                          parent=folderid)):
        raise WeasylError("parentidInvalid")

    if parentid > 0:
        parent_query = d.execute(
            "SELECT folderid, parentid, userid, title FROM folder WHERE folderid = %i",
            [parentid])

        if not parent_query:
            raise WeasylError("folderRecordMissing")
        # parent folder itself cannot be a subfolder
        elif parent_query[0][1] > 0:
            raise WeasylError("parentidInvalid")
        # folder cannot be a subfolder of another user's folder
        elif userid != parent_query[0][2]:
            raise WeasylError("InsufficientPermissions")
        # folder cannot share title with parent folder
        elif folder_query[0][3] == parent_query[0][3]:
            raise WeasylError("folderRecordExists")

    # folder cannot share title within parent folder
    for folder in d.execute("SELECT title FROM folder WHERE parentid = %i AND userid = %i", [parentid, userid]):
        if folder_query[0][3] == folder[0]:
            raise WeasylError("folderRecordExists")

    d.execute("UPDATE folder SET parentid = %i WHERE folderid = %i",
              [parentid, folderid])


def remove(userid, folderid):
    # Check folder exists and user owns it
    query = d.engine.scalar("SELECT userid FROM folder WHERE folderid = %(folder)s",
                            folder=folderid)

    if not query:
        raise WeasylError("folderRecordMissing")
    elif userid != query:
        raise WeasylError("InsufficientPermissions")

    with d.engine.begin() as db:
        # Hide folders
        db.execute("UPDATE folder SET settings = settings || 'h' WHERE (folderid = %(id)s OR parentid = %(id)s) AND settings !~ 'h'", id=folderid)

        # Move submissions to root
        db.execute("UPDATE submission SET folderid = NULL FROM folder WHERE submission.folderid = folder.folderid AND (folder.folderid = %(id)s OR folder.parentid = %(id)s)", id=folderid)

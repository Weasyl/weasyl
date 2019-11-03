from __future__ import absolute_import

import sqlalchemy as sa

from libweasyl import staff

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
            return d.execute(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (folderid, userid) = (%i, %i) AND settings !~ 'h')",
                [folderid, userid], option="bool")
        else:
            return d.execute(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (folderid, userid, parentid) = (%i, %i, %i) AND settings !~ 'h')",
                [folderid, userid, parentid], option="bool")
    elif title:
        if parentid is None:
            return d.execute(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (userid, title) = (%i, '%s') AND settings !~ 'h')",
                [userid, title], option="bool")
        else:
            return d.execute(
                "SELECT EXISTS (SELECT 0 FROM folder WHERE (userid, parentid, title) = (%i, %i, '%s') AND settings !~ 'h')",
                [userid, parentid, title], option="bool")


# form
#   title
#   parentid

def create(userid, form):
    form.title = form.title.strip()[:_TITLE]
    form.parentid = d.get_int(form.parentid)

    if not check(userid, form.parentid, parentid=0, root=True):
        raise WeasylError("folderRecordMissing")
    elif not form.title.strip():
        raise WeasylError("titleInvalid")
    elif check(userid, title=form.title, parentid=form.parentid):
        raise WeasylError("folderRecordExists")

    return d.execute("INSERT INTO folder (parentid, userid, title) VALUES (%i, %i, '%s') RETURNING folderid",
                     [form.parentid, userid, form.title])


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


# feature
#   "drop/parents"
#   "drop/all"
#   "sidebar/all"

def select_list(userid, feature):
    result = []

    # Select for sidebar
    if feature == "sidebar/all":
        query = d.execute("""
            SELECT
                fd.folderid, fd.title, fd.parentid,
                (SELECT COUNT(*) FROM submission WHERE folderid = fd.folderid AND settings !~ 'h')
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
                "count": query[i][3],
                "thumb": "",
            })

            for j in range(i + 1, len(query)):
                if query[j][2] == query[i][0]:
                    result.append({
                        "folderid": query[j][0],
                        "title": query[j][1],
                        "subfolder": True,
                        "count": query[j][3],
                        "thumb": "",
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


# form
#   folderid
#   title

def rename(userid, form):
    form.title = form.title.strip()[:_TITLE]
    form.folderid = d.get_int(form.folderid)

    query = d.execute("SELECT userid FROM folder WHERE folderid = %i",
                      [form.folderid], option="element")

    if not query:
        raise WeasylError("folderRecordMissing")
    elif not form.title:
        raise WeasylError("titleInvalid")
    elif userid != query and userid not in staff.ADMINS:
        raise WeasylError("InsufficientPermissions")

    d.execute("UPDATE folder SET title = '%s' WHERE folderid = %i",
              [form.title, form.folderid])


# form
#   folderid
#   parentid

def move(userid, form):
    form.folderid = d.get_int(form.folderid)
    form.parentid = d.get_int(form.parentid)

    folder_query = d.execute(
        "SELECT folderid, parentid, userid, title FROM folder WHERE folderid = %i",
        [form.folderid])

    if not folder_query:
        raise WeasylError("folderRecordMissing")
    # folder cannot be a subfolder of itself
    elif form.folderid == form.parentid:
        raise WeasylError("parentidInvalid")
    # folder cannot be a subfolder of another user's folder
    elif userid != folder_query[0][2]:
        raise WeasylError("InsufficientPermissions")
    # folder with subfolders cannot become a subfolder
    elif (form.folderid and
          d.execute("SELECT EXISTS (SELECT 0 FROM folder WHERE parentid = %i)",
                    [form.folderid], option="bool")):
        raise WeasylError("parentidInvalid")

    if form.parentid > 0:
        parent_query = d.execute(
            "SELECT folderid, parentid, userid, title FROM folder WHERE folderid = %i",
            [form.parentid])

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
    for folder in d.execute("SELECT title FROM folder WHERE parentid = %i AND userid = %i", [form.parentid, userid]):
        if folder_query[0][3] == folder[0]:
            raise WeasylError("folderRecordExists")

    d.execute("UPDATE folder SET parentid = %i WHERE folderid = %i",
              [form.parentid, form.folderid])


def remove(userid, folderid):
    # Check folder exists and user owns it
    query = d.execute("SELECT userid FROM folder WHERE folderid = %i",
                      [folderid], option="element")

    if not query:
        raise WeasylError("folderRecordMissing")
    elif userid != query:
        raise WeasylError("InsufficientPermissions")

    # Select relevant unhidden folders
    folders = d.sql_number_list(
        [folderid] +
        d.execute("SELECT folderid FROM folder WHERE parentid = %i AND settings !~ 'h'", [folderid], option="within"))

    # Hide folders
    d.execute("UPDATE folder SET settings = settings || 'h' WHERE folderid IN %s AND settings !~ 'h'", [folders])

    # Move submissions to root
    d.execute("UPDATE submission SET folderid = NULL WHERE folderid IN %s", [folders])

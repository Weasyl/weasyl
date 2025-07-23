from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import staff
from weasyl import comment, define, profile, siteupdate
from weasyl.error import WeasylError
from weasyl.controllers.decorators import admin_only, token_checked
import weasyl.define as d


_BLANK_SITE_UPDATE = {
    'updateid': None,
    'title': "",
    'content': "",
    'wesley': False,
}


def site_update_list_(request):
    userid = request.userid
    updates = siteupdate.select_list()
    can_post = userid in staff.ADMINS

    if updates and userid:
        last_read_updateid = d.get_last_read_updateid(userid) or 0
        max_updateid = updates[0]['updateid']

        if max_updateid > last_read_updateid:
            d.engine.execute("""
                UPDATE login
                SET last_read_updateid = %(max)s
                WHERE userid = %(user)s
            """, max=max_updateid, user=userid)

            d.get_last_read_updateid.invalidate(userid)
    else:
        last_read_updateid = None

    return Response(define.webpage(
        request.userid,
        'siteupdates/list.html',
        (request, updates, can_post, last_read_updateid),
        title="Site Updates",
    ))


def site_update_get_(request):
    userid = request.userid
    updateid = int(request.matchdict['update_id'])
    update = siteupdate.select_view(updateid)
    myself = profile.select_myself(userid)
    comments = comment.select(userid, updateid=updateid)

    if userid:
        d.engine.execute("""
            UPDATE login
            SET last_read_updateid = %(updateid)s
            WHERE userid = %(userid)s
            AND COALESCE(last_read_updateid, 0) < %(updateid)s
        """, userid=userid, updateid=updateid)
        d.get_last_read_updateid.invalidate(userid)

    return Response(define.webpage(userid, 'siteupdates/detail.html', (myself, update, comments), title="Site Update"))


@admin_only
@token_checked
def site_update_put_(request):
    updateid = int(request.matchdict['update_id'])
    title = request.POST["title"].strip()
    content = request.POST["content"].strip()
    wesley = "wesley" in request.POST

    if not title:
        raise WeasylError("titleInvalid")

    if not content:
        raise WeasylError("contentInvalid")

    siteupdate.edit(
        updateid=updateid,
        title=title,
        content=content,
        wesley=wesley,
    )

    return HTTPSeeOther(location="/site-updates/%d" % (updateid,))


@admin_only
def site_update_new_get_(request):
    return Response(d.webpage(request.userid, "siteupdates/form.html", (_BLANK_SITE_UPDATE,), title="Submit Site Update"))


@admin_only
@token_checked
def site_update_post_(request):
    title = request.POST["title"].strip()
    content = request.POST["content"].strip()
    wesley = "wesley" in request.POST

    if not title:
        raise WeasylError("titleInvalid")

    if not content:
        raise WeasylError("contentInvalid")

    updateid = siteupdate.create(
        userid=request.userid,
        title=title,
        content=content,
        wesley=wesley,
    )

    d.get_updateids.invalidate()

    raise HTTPSeeOther(location="/site-updates/%d" % (updateid,))


@admin_only
def site_update_edit_(request):
    updateid = int(request.matchdict['update_id'])
    update = siteupdate.select_view(updateid)
    return Response(d.webpage(request.userid, "siteupdates/form.html", (update,), title="Edit Site Update"))

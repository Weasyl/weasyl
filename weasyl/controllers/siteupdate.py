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
    updates = siteupdate.select_list()
    can_post = request.userid in staff.ADMINS

    return Response(define.webpage(request.userid, 'siteupdates/list.html', (request, updates, can_post), title="Site Updates"))


def site_update_get_(request):
    updateid = int(request.matchdict['update_id'])
    update = siteupdate.select_view(updateid)
    myself = profile.select_myself(request.userid)
    comments = comment.select(request.userid, updateid=updateid)

    return Response(define.webpage(request.userid, 'siteupdates/detail.html', (myself, update, comments), title="Site Update"))


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

    raise HTTPSeeOther(location="/site-updates/%d" % (updateid,))


@admin_only
def site_update_edit_(request):
    updateid = int(request.matchdict['update_id'])
    update = siteupdate.select_view(updateid)
    return Response(d.webpage(request.userid, "siteupdates/form.html", (update,), title="Edit Site Update"))

from __future__ import absolute_import

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import staff
from libweasyl.models.site import SiteUpdate

from weasyl import login, moderation, profile, siteupdate
from weasyl.error import WeasylError
from weasyl.controllers.decorators import admin_only
from weasyl.controllers.decorators import token_checked
import weasyl.define as d


""" Administrator control panel view callables """


@admin_only
def admincontrol_(request):
    return Response(d.webpage(request.userid, "admincontrol/admincontrol.html", title="Admin Control Panel"))


@admin_only
def admincontrol_siteupdate_get_(request):
    return Response(d.webpage(request.userid, "admincontrol/siteupdate.html", (SiteUpdate(),), title="Submit Site Update"))


@admin_only
@token_checked
def admincontrol_siteupdate_post_(request):
    title = request.params["title"].strip()
    content = request.params["content"].strip()
    wesley = "wesley" in request.params

    if not title:
        raise WeasylError("titleInvalid")

    if not content:
        raise WeasylError("contentInvalid")

    update = siteupdate.create(request.userid, title, content, wesley=wesley)
    raise HTTPSeeOther(location="/site-updates/%d" % (update.updateid,))


@admin_only
def site_update_edit_(request):
    updateid = int(request.matchdict['update_id'])
    update = SiteUpdate.query.get_or_404(updateid)
    return Response(d.webpage(request.userid, "admincontrol/siteupdate.html", (update,), title="Edit Site Update"))


@admin_only
@token_checked
def site_update_put_(request):
    updateid = int(request.matchdict['update_id'])
    title = request.params["title"].strip()
    content = request.params["content"].strip()
    wesley = "wesley" in request.params

    if not title:
        raise WeasylError("titleInvalid")

    if not content:
        raise WeasylError("contentInvalid")

    update = SiteUpdate.query.get_or_404(updateid)
    update.title = title
    update.content = content
    update.wesley = wesley
    update.dbsession.flush()

    raise HTTPSeeOther(location="/site-updates/%d" % (update.updateid,))


@admin_only
def admincontrol_manageuser_get_(request):
    form = request.web_input(name="")
    otherid = profile.resolve(None, None, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    if request.userid != otherid and otherid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        raise WeasylError('InsufficientPermissions')

    return Response(d.webpage(request.userid, "admincontrol/manageuser.html", [
        # Manage user information
        profile.select_manage(otherid),
    ], title="User Management"))


@admin_only
@token_checked
def admincontrol_manageuser_post_(request):
    form = request.web_input(ch_username="", ch_full_name="", ch_catchphrase="", ch_email="",
                             ch_birthday="", ch_gender="", ch_country="", remove_social=[])
    userid = d.get_int(form.userid)

    if request.userid != userid and userid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        raise WeasylError('InsufficientPermissions')

    profile.do_manage(request.userid, userid,
                      username=form.username.strip() if form.ch_username else None,
                      full_name=form.full_name.strip() if form.ch_full_name else None,
                      catchphrase=form.catchphrase.strip() if form.ch_catchphrase else None,
                      birthday=form.birthday if form.ch_birthday else None,
                      gender=form.gender if form.ch_gender else None,
                      country=form.country if form.ch_country else None,
                      remove_social=form.remove_social,
                      permission_tag='permission-tag' in form)
    raise HTTPSeeOther(location="/admincontrol")


@admin_only
@token_checked
def admincontrol_acctverifylink_(request):
    form = request.web_input(username="", email="")

    token = login.get_account_verification_token(
        username=form.username, email=form.email)

    if token:
        return Response(d.webpage(request.userid, "admincontrol/acctverifylink.html", [token]))

    return Response(d.errorpage(request.userid, "No pending account found."))


@admin_only
def admincontrol_pending_accounts_get_(request):
    """
    Retrieve a listing of any active pending accounts in the logincreate table.

    :param request: The Pyramid request object.
    :return: A Pyramid response with a webpage containing the pending accounts.
    """
    query = d.engine.execute("""
        SELECT token, username, email, invalid, invalid_email_addr, created_at
        FROM logincreate
        ORDER BY username
    """).fetchall()

    return Response(d.webpage(
        request.userid,
        "admincontrol/pending_accounts.html",
        [query],
        title="Accounts Pending Creation"
    ))


@admin_only
@token_checked
def admincontrol_pending_accounts_post_(request):
    """
    Purges a specified logincreate record.

    :param request: A Pyramid request.
    :return: HTTPSeeOther to /admincontrol/pending_accounts
    """
    logincreatetoken = request.POST.get("logincreatetoken")
    if logincreatetoken:
        d.engine.execute("""
            DELETE FROM logincreate
            WHERE token = %(token)s
        """, token=logincreatetoken)

    raise HTTPSeeOther(location="/admincontrol/pending_accounts")


@admin_only
def admincontrol_finduser_get_(request):
    return Response(d.webpage(request.userid, "admincontrol/finduser.html", title="Search Users"))


@admin_only
@token_checked
def admincontrol_finduser_post_(request):
    form = request.web_input(userid="", username="", email="", excludebanned="", excludesuspended="", excludeactive="",
                             dateafter="", datebefore="", row_offset=0, ipaddr="")

    # Redirect negative row offsets (PSQL errors on negative offset values)
    if int(form.row_offset) < 0:
        raise HTTPSeeOther("/admincontrol/finduser")

    return Response(d.webpage(request.userid, "admincontrol/finduser.html", [
        # Search results
        moderation.finduser(request.userid, form),
        # Pass the form and row offset in to enable pagination
        form,
        int(form.row_offset)
    ], title="Search Users: Results"))

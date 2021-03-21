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
    otherid = profile.resolve(None, None, request.params.get('name', ''))

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
    userid = d.get_int(request.params.get('userid', ''))

    if request.userid != userid and userid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        raise WeasylError('InsufficientPermissions')

    profile.do_manage(request.userid, userid,
                      username=request.params.get('username', '').strip() if 'ch_username' in request.params else None,
                      full_name=request.params.get('full_name', '').strip() if 'ch_full_name' in request.params else None,
                      catchphrase=request.params.get('catchphrase', '').strip() if 'ch_catchphrase' in request.params else None,
                      birthday=request.params.get('birthday', '') if 'ch_birthday' in request.params else None,
                      gender=request.params.get('gender', '') if 'ch_gender' in request.params else None,
                      country=request.params.get('country', '') if 'ch_country' in request.params else None,
                      remove_social=request.params.getall('remove_social'),
                      permission_tag='permission-tag' in request.params)
    raise HTTPSeeOther(location="/admincontrol")


@admin_only
@token_checked
def admincontrol_acctverifylink_(request):
    token = login.get_account_verification_token(
        username=request.params.get('username', ''), email=request.params.get('email', ''))

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
    row_offset = int(request.params.get('row_offset', 0))
    # Redirect negative row offsets (PSQL errors on negative offset values)
    if row_offset < 0:
        raise HTTPSeeOther("/admincontrol/finduser")

    form = {
        'targetid': request.params.get('targetid', ''),
        'username': request.params.get('username', '').strip(),
        'email': request.params.get('email', '').strip(),
        'excludebanned': request.params.get('excludebanned', ''),
        'excludesuspended': request.params.get('excludesuspended', ''),
        'excludeactive': request.params.get('excludeactive', ''),
        'dateafter': request.params.get('dateafter', ''),
        'datebefore': request.params.get('datebefore', ''),
        'ipaddr': request.params.get('ipaddr', ''),
        'row_offset': row_offset,
    }

    return Response(d.webpage(request.userid, "admincontrol/finduser.html", [
        # Search results
        moderation.finduser(**form),
        # Pass the form and row offset in to enable pagination
        form,
        row_offset
    ], title="Search Users: Results"))

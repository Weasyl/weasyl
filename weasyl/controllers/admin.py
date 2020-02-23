from __future__ import absolute_import

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from libweasyl import staff
from libweasyl.models.site import SiteUpdate

from weasyl import login, moderation, profile, siteupdate
from weasyl.error import WeasylError
from weasyl.controllers.decorators import admin_only
from weasyl.controllers.decorators import token_checked
import weasyl.define as d


""" Administrator control panel view callables """


@view_config(route_name="admincontrol", renderer='/admincontrol/admincontrol.jinja2')
@admin_only
def admincontrol_(request):
    return {'title': "Admin Control Panel"}


@view_config(route_name="admin_siteupdate", renderer='/admincontrol/siteupdate.jinja2', request_method="GET")
@admin_only
def admincontrol_siteupdate_get_(request):
    return {'update': SiteUpdate(), 'title': "Submit Site Update"}


@view_config(route_name="admin_siteupdate", renderer='/admincontrol/siteupdate.jinja2', request_method="POST")
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


@view_config(route_name="site_update_edit", renderer='/admincontrol/siteupdate.jinja2', request_method="GET")
@admin_only
def site_update_edit_(request):
    updateid = int(request.matchdict['update_id'])
    update = SiteUpdate.query.get_or_404(updateid)
    return {'update': update, 'title': "Edit Site Update"}


@view_config(route_name="site_update", renderer='/admincontrol/siteupdate.jinja2', request_method="POST")
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


@view_config(route_name="admin_manageuser", renderer='/admincontrol/manageuser.jinja2', request_method="GET")
@admin_only
def admincontrol_manageuser_get_(request):
    form = request.web_input(name="")
    otherid = profile.resolve(None, None, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    if request.userid != otherid and otherid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        raise WeasylError('permission')

    return {'profile': profile.select_manage(otherid), 'title': "User Management"}


@view_config(route_name="admin_manageuser", renderer='/admincontrol/manageuser.jinja2', request_method="POST")
@admin_only
@token_checked
def admincontrol_manageuser_post_(request):
    form = request.web_input(ch_username="", ch_full_name="", ch_catchphrase="", ch_email="",
                             ch_birthday="", ch_gender="", ch_country="", remove_social=[])
    userid = d.get_int(form.userid)

    if request.userid != userid and userid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        raise WeasylError('permission')

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


@view_config(route_name="admin_acctverifylink", renderer='/admincontrol/acctverifylink.jinja2', request_method="POST")
@admin_only
@token_checked
def admincontrol_acctverifylink_(request):
    form = request.web_input(username="", email="")

    token = login.get_account_verification_token(
        username=form.username, email=form.email)

    if token:
        return {'token': token}

    return {'message': "No pending account found."}


@view_config(route_name="admincontrol_pending_accounts", renderer='/admincontrol/pending_accounts.jinja2', request_method="GET")
@admin_only
def admincontrol_pending_accounts_get_(request):
    """
    Retrieve a listing of any active pending accounts in the logincreate table.

    :param request: The Pyramid request object.
    :return: A Pyramid response with a webpage containing the pending accounts.
    """
    query = d.engine.execute("""
        SELECT token, username, email, invalid, invalid_email_addr, unixtime
        FROM logincreate
        ORDER BY username
    """).fetchall()

    return {'query': query, 'title': "Accounts Pending Creation"}


@view_config(route_name="admincontrol_pending_accounts", renderer='/admincontrol/pending_accounts.jinja2', request_method="POST")
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


@view_config(route_name="admincontrol_finduser",  renderer='/admincontrol/finduser.jinja2', request_method="GET")
@admin_only
def admincontrol_finduser_get_(request):
    return {'title': "Search Users"}


@view_config(route_name="admincontrol_finduser",  renderer='/admincontrol/finduser.jinja2', request_method="POST")
@admin_only
@token_checked
def admincontrol_finduser_post_(request):
    form = request.web_input(userid="", username="", email="", excludebanned="", excludesuspended="", excludeactive="",
                             dateafter="", datebefore="", row_offset=0, ipaddr="")

    # Redirect negative row offsets (PSQL errors on negative offset values)
    if int(form.row_offset) < 0:
        raise HTTPSeeOther("/admincontrol/finduser")

    return {
        'query': moderation.finduser(request.userid, form),
        'form': form,
        'row_offset': int(form.row_offset),
        'title': "Search Users: Results"
    }

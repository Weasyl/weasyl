from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import staff

from weasyl import dry, errorcode, login, profile, siteupdate, moderation
from weasyl.error import WeasylError
from weasyl.controllers.decorators import admin_only
from weasyl.controllers.decorators import moderator_only
from weasyl.controllers.decorators import token_checked
import weasyl.define as d


""" Administrator control panel view callables """


@admin_only
def admincontrol_(request):
    return Response(dry.admin_render_page("admincontrol/admincontrol.html"))


@moderator_only
def admincontrol_siteupdate_get_(request):
    return Response(dry.admin_render_page("admincontrol/siteupdate.html"))


@token_checked
@moderator_only
def admincontrol_siteupdate_post_(request):
    form = request.web_input(title="", content="")

    siteupdate.create(request.userid, form)

    raise HTTPSeeOther(location="/admincontrol")


@admin_only
def admincontrol_manageuser_get_(request):
    form = request.web_input(name="")
    otherid = profile.resolve(None, None, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    if request.userid != otherid and otherid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        return Response(d.errorpage(request.userid, errorcode.permission))

    return Response(d.webpage(request.userid, "admincontrol/manageuser.html", [
        # Manage user information
        profile.select_manage(otherid),
        # only technical staff can impersonate users
        request.userid in staff.TECHNICAL,
    ]))


@token_checked
@admin_only
def admincontrol_manageuser_post_(request):
    form = request.web_input(ch_username="", ch_full_name="", ch_catchphrase="", ch_email="",
                             ch_birthday="", ch_gender="", ch_country="", remove_social=[])
    userid = d.get_int(form.userid)

    if request.userid != userid and userid in staff.ADMINS and request.userid not in staff.TECHNICAL:
        return d.errorpage(request.userid, errorcode.permission)
    if form.get('impersonate'):
        if request.userid not in staff.TECHNICAL:
            return d.errorpage(request.userid, errorcode.permission)
        sess = request.weasyl_session
        sess.additional_data.setdefault('user-stack', []).append(sess.userid)
        sess.additional_data.changed()
        sess.userid = userid
        sess.save = True
        d.append_to_log(
            'staff.actions', userid=request.userid, action='impersonate', target=userid)
        raise HTTPSeeOther(location="/")
    else:
        profile.do_manage(request.userid, userid,
                          username=form.username.strip() if form.ch_username else None,
                          full_name=form.full_name.strip() if form.ch_full_name else None,
                          catchphrase=form.catchphrase.strip() if form.ch_catchphrase else None,
                          birthday=form.birthday if form.ch_birthday else None,
                          gender=form.gender if form.ch_gender else None,
                          country=form.country if form.ch_country else None,
                          remove_social=form.remove_social if form.remove_social else None)
        raise HTTPSeeOther(location="/admincontrol")


@token_checked
@admin_only
def admincontrol_acctverifylink_(request):
    form = request.web_input(username="", email="")

    token = login.get_account_verification_token(
        username=form.username, email=form.email)

    if token:
        return Response(d.webpage(request.userid, "admincontrol/acctverifylink.html", [token]))

    return Response(d.errorpage(request.userid, "No pending account found."))


@admin_only
def admincontrol_finduser_get_(request):
    return Response(d.webpage(request.userid, "admincontrol/finduser.html"))


@admin_only
@token_checked
def admincontrol_finduser_post_(request):
    form = request.web_input(userid="", username="", email="")

    return Response(d.webpage(request.userid, "admincontrol/finduser.html", [
        # Search results
        moderation.finduser(request.userid, form)
    ]))

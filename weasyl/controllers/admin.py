import web

from libweasyl import staff

from weasyl import dry, errorcode, login, profile, siteupdate
from weasyl.error import WeasylError
from weasyl.controllers.decorators import controller_base
import weasyl.define as d


# Administrator control panel functions
class admincontrol_(controller_base):
    login_required = True
    admin_only = True

    def GET(self):
        return dry.admin_render_page("admincontrol/admincontrol.html")


admincontrol_siteupdate_ = siteupdate.admincontrol_siteupdate_


class admincontrol_manageuser_(controller_base):
    login_required = True
    admin_only = True

    def GET(self):
        form = web.input(name="")
        otherid = profile.resolve(None, None, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        if self.user_id != otherid and otherid in staff.ADMINS and self.user_id not in staff.TECHNICAL:
            return d.errorpage(self.user_id, errorcode.permission)

        return d.webpage(self.user_id, "admincontrol/manageuser.html", [
            # Manage user information
            profile.select_manage(otherid),
            # only technical staff can impersonate users
            self.user_id in staff.TECHNICAL,
        ])

    @d.token_checked
    def POST(self):
        form = web.input(ch_username="", ch_full_name="", ch_catchphrase="", ch_email="",
                         ch_birthday="", ch_gender="", ch_country="")
        userid = d.get_int(form.userid)

        if self.user_id != userid and userid in staff.ADMINS and self.user_id not in staff.TECHNICAL:
            return d.errorpage(self.user_id, errorcode.permission)
        if form.get('impersonate'):
            if self.user_id not in staff.TECHNICAL:
                return d.errorpage(self.user_id, errorcode.permission)
            sess = web.ctx.weasyl_session
            sess.additional_data.setdefault('user-stack', []).append(sess.userid)
            sess.additional_data.changed()
            sess.userid = userid
            sess.save = True
            d.append_to_log(
                'staff.actions', userid=self.user_id, action='impersonate', target=userid)
            raise web.seeother('/')
        else:
            profile.do_manage(self.user_id, userid,
                              username=form.username.strip() if form.ch_username else None,
                              full_name=form.full_name.strip() if form.ch_full_name else None,
                              catchphrase=form.catchphrase.strip() if form.ch_catchphrase else None,
                              birthday=form.birthday if form.ch_birthday else None,
                              gender=form.gender if form.ch_gender else None,
                              country=form.country if form.ch_country else None)
            raise web.seeother("/admincontrol")


class admincontrol_acctverifylink_(controller_base):
    login_required = True
    admin_only = True

    @d.token_checked
    def POST(self):
        form = web.input(username="", email="")

        token = login.get_account_verification_token(
            username=form.username, email=form.email)

        if token:
            return d.webpage(self.user_id, "admincontrol/acctverifylink.html", [token])

        return d.errorpage(self.user_id, "No pending account found.")

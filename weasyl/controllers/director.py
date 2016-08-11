import web

from libweasyl import staff

from weasyl import dry, errorcode, login, profile, siteupdate
from weasyl.error import WeasylError
from weasyl.controllers.base import controller_base
import weasyl.define as d


# Director control panel functions
class directorcontrol_(controller_base):
    login_required = True
    director_only = True

    def GET(self):
        return dry.admin_render_page("directorcontrol/directorcontrol.html")
    
    @d.token_checked
    def POST(self):
        form = web.input(target_username=None, action=None)
        target_user_id = profile.resolve(None, None, form.target_username)

        if form.action == "impersonate":
            # Verify that the target user exists; else, raise an error
            if not target_user_id:
                return d.errorpage(self.user_id, "Invalid username supplied; you should go back and try again.")
            sess = web.ctx.weasyl_session
            sess.additional_data.setdefault('user-stack', []).append(sess.userid)
            sess.additional_data.changed()
            sess.userid = target_user_id
            sess.save = True
            d.append_to_log(
                'staff.actions', userid=self.user_id, action='impersonate', target=target_user_id)
            raise web.seeother('/')

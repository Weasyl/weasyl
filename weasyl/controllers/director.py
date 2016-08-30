from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import dry, profile
from weasyl.controllers.decorators import director_only
from weasyl.controllers.decorators import token_checked
import weasyl.define as d


""" Director control panel view callables """


@director_only
def directorcontrol_get_(request):
    return Response(dry.admin_render_page("directorcontrol/directorcontrol.html"))


@token_checked
@director_only
def directorcontrol_post_(request):
    form = request.web_input(target_username=None, action=None)
    target_user_id = profile.resolve(None, None, form.target_username)

    if form.action == "impersonate":
        # Verify that the target user exists; else, raise an error
        if not target_user_id:
            return Response(d.errorpage(request.userid, "Invalid username supplied; you should go back and try again."))
        sess = request.weasyl_session
        sess.additional_data.setdefault('user-stack', []).append(sess.userid)
        sess.additional_data.changed()
        sess.userid = target_user_id
        sess.save = True
        d.append_to_log(
            'staff.actions', userid=request.userid, action='impersonate', target=target_user_id)
        raise HTTPSeeOther(location="/")

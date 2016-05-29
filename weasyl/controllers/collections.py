import web

from weasyl import define, collection, profile
from weasyl.error import WeasylError
from weasyl.controllers.base import controller_base


class collection_options_(controller_base):
    login_required = True

    def GET(self):
        jsonb_settings = define.get_profile_settings(self.user_id)
        form_settings = {
            "allow_request": jsonb_settings.allow_collection_requests,
            "allow_notification": jsonb_settings.allow_collection_notifs,
        }
        return define.webpage(self.user_id, "manage/collection_options.html", [form_settings])

    @define.token_checked
    def POST(self):
        form = web.input(allow_request="", allow_notification="")

        jsonb_settings = define.get_profile_settings(self.user_id)
        jsonb_settings.allow_collection_requests = form.allow_request
        jsonb_settings.allow_collection_notifs = form.allow_notification

        profile.edit_preferences(self.user_id, jsonb_settings=jsonb_settings)
        raise web.seeother("/control")


class collection_offer_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", username="")
        form.otherid = profile.resolve(None, None, form.username)
        form.submitid = int(form.submitid)

        if not form.otherid:
            raise WeasylError("UserRecordMissing")
        if self.user_id == form.otherid:
            raise WeasylError("cannotSelfCollect")

        collection.offer(self.user_id, form.submitid, form.otherid)
        return define.errorpage(
            self.user_id,
            "**Success!** Your collection offer has been sent "
            "and the recipient may now add this submission to their gallery.",
            [["Go Back", "/submission/%i" % (form.submitid,)], ["Return to the Home Page", "/index"]])


class collection_request_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="")
        form.submitid = int(form.submitid)
        form.otherid = define.get_ownerid(submitid=form.submitid)

        if not form.otherid:
            raise WeasylError("UserRecordMissing")
        if self.user_id == form.otherid:
            raise WeasylError("cannotSelfCollect")

        collection.request(self.user_id, form.submitid, form.otherid)
        return define.errorpage(
            self.user_id,
            "**Success!** Your collection request has been sent. "
            "The submission author may approve or reject this request.",
            [["Go Back", "/submission/%i" % (form.submitid,)], ["Return to the Home Page", "/index"]])


class collection_remove_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submissions=[])
        # submissions input format: "submissionID;collectorID"
        submissions = [int(x.split(";")[0]) for x in form.submissions]

        collection.remove(self.user_id, submissions)
        raise web.seeother("/manage/collections")

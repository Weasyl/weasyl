import web

import anyjson as json

from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import define, macro, moderation, report


# Moderator control panel functions
class modcontrol_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        return define.webpage(self.user_id, "modcontrol/modcontrol.html")


class modcontrol_finduser_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        return define.webpage(self.user_id, "modcontrol/finduser.html")

    @define.token_checked
    def POST(self):
        form = web.input(userid="", username="", email="")

        return define.webpage(self.user_id, "modcontrol/finduser.html", [
            # Search results
            moderation.finduser(self.user_id, form)
        ])


class modcontrol_suspenduser_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        return define.webpage(self.user_id, "modcontrol/suspenduser.html",
                              [moderation.BAN_TEMPLATES, json.dumps(moderation.BAN_TEMPLATES)])

    @define.token_checked
    def POST(self):
        form = web.input(userid="", username="", mode="", reason="", day="", month="", year="", datetype="",
                         duration="", durationunit="")

        moderation.setusermode(self.user_id, form)
        raise web.seeother("/modcontrol")


class modcontrol_report_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        form = web.input(reportid='')
        r = report.select_view(self.user_id, form)
        blacklisted_tags = moderation.gallery_blacklisted_tags(self.user_id, r.target.userid)

        return define.webpage(self.user_id, "modcontrol/report.html", [
            self.user_id,
            r,
            blacklisted_tags,
        ])


class modcontrol_reports_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        form = web.input(status="open", violation="", submitter="")
        return define.webpage(self.user_id, "modcontrol/reports.html", [
            # Method
            {"status": form.status, "violation": int(form.violation or -1), "submitter": form.submitter},
            # Reports
            report.select_list(self.user_id, form),
            macro.MACRO_REPORT_VIOLATION,
        ])

    POST = GET


class modcontrol_closereport_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(reportid='', action='')
        report.close(self.user_id, form)
        raise web.seeother("/modcontrol/report?reportid=%s" % (form.reportid,))


class modcontrol_contentbyuser_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        form = web.input(name='', features=[])

        submissions = moderation.submissionsbyuser(self.user_id, form) if 's' in form.features else []
        characters = moderation.charactersbyuser(self.user_id, form) if 'c' in form.features else []
        journals = moderation.journalsbyuser(self.user_id, form) if 'j' in form.features else []

        return define.webpage(self.user_id, "modcontrol/contentbyuser.html", [
            form.name,
            sorted(submissions + characters + journals, key=lambda item: item['unixtime'], reverse=True),
        ])


class modcontrol_massaction_(controller_base):
    login_required = True
    moderator_only = True

    def POST(self):
        form = web.input(action='', name='', submissions=[], characters=[], journals=[])
        if form.action.startswith("zap-"):
            # "Zapping" cover art or thumbnails is not a bulk edit.
            if not form.submissions:
                raise WeasylError("Unexpected")
            submitid = int(form.submissions[0])
            type = form.action.split("zap-")[1]
            if type == "cover":
                moderation.removecoverart(self.user_id, submitid)
            elif type == "thumb":
                moderation.removethumbnail(self.user_id, submitid)
            elif type == "both":
                moderation.removecoverart(self.user_id, submitid)
                moderation.removethumbnail(self.user_id, submitid)
            else:
                raise WeasylError("Unexpected")
            raise web.seeother("/submission/%i" % (submitid,))

        return moderation.bulk_edit(
            self.user_id,
            form.action,
            map(int, form.submissions),
            map(int, form.characters),
            map(int, form.journals),
        )


class modcontrol_hide_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(name="", submission="", character="")

        if form.submission:
            moderation.hidesubmission(int(form.submission))
        elif form.character:
            moderation.hidecharacter(int(form.character))

        raise web.seeother("/modcontrol")


class modcontrol_unhide_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(name="", submission="", character="")

        if form.submission:
            moderation.unhidesubmission(int(form.submission))
        elif form.character:
            moderation.unhidecharacter(int(form.character))

        raise web.seeother("/modcontrol")


class modcontrol_manageuser_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        form = web.input(name="")

        return define.webpage(self.user_id, "modcontrol/manageuser.html", [
            moderation.manageuser(self.user_id, form),
        ])


class modcontrol_removeavatar_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")

        moderation.removeavatar(self.user_id, define.get_int(form.userid))
        raise web.seeother("/modcontrol")


class modcontrol_removebanner_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")

        moderation.removebanner(self.user_id, define.get_int(form.userid))
        raise web.seeother("/modcontrol")


class modcontrol_editprofiletext_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="", content="")

        moderation.editprofiletext(self.user_id, define.get_int(form.userid), form.content)
        raise web.seeother("/modcontrol")


class modcontrol_editcatchphrase_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="", content="")

        moderation.editcatchphrase(self.user_id, define.get_int(form.userid), form.content)
        raise web.seeother("/modcontrol")


class modcontrol_edituserconfig_(controller_base):
    login_required = True
    moderator_only = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")

        moderation.edituserconfig(form)
        raise web.seeother("/modcontrol")

import web

from datetime import datetime
from libweasyl import staff
from weasyl import ads
from weasyl import define
from weasyl.controllers.base import controller_base
from weasyl.define import token_checked
from weasyl.error import WeasylError


class create_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self):
        return define.render("ads/create.html", [None])

    @token_checked
    def POST(self):
        form = web.input(image="", owner="", end="")

        try:
            form.end = datetime.strptime(form.end, "%Y-%m-%d")
        except ValueError:
            raise WeasylError("adEndDateInvalid")

        ad_id = ads.create_ad(form)
        return define.render("ads/create.html", (ad_id,))


class list_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "ads/list.html", [self.user_id, ads.get_current_ads()])

    @token_checked
    def POST(self):
        form = web.input(takedown="")

        if form.takedown:
            ad_id = int(form.takedown)

            if self.user_id not in staff.MODS:
                raise WeasylError("InsufficientPermissions")

            ads.expire(ad_id)

        raise web.seeother("/ads")

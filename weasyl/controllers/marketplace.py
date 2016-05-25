import itertools
import time

import web

from weasyl import define, media, commishinfo, profile
from weasyl.controllers.base import controller_base


class search_(controller_base):
    cache_name = "etc/marketplace.html"

    def GET(self):

        form = web.input(q="", min="", max="")
        results = profile.select_commissionable(self.user_id,
                                                form.q,
                                                commishinfo.convert_currency(form.min),
                                                commishinfo.convert_currency(form.max),
                                                30)
        media.populate_with_user_media(results)
        return define.webpage(self.user_id, "etc/marketplace.html", [results, form])


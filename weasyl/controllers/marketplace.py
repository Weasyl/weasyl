import itertools
import time

import web

from weasyl import define, media, commishinfo
from weasyl.controllers.base import controller_base


class search_(controller_base):
    cache_name = "etc/marketplace.html"

    def GET(self):
        form = web.input(q="", min="", max="", currency="", pc="", c="")
        commishclass = form.c if form.c else form.pc
        form.c = commishclass
        commishclass = commishclass.lower()

        results = commishinfo.select_commissionable(self.user_id,
                                                    form.q,
                                                    commishclass,
                                                    commishinfo.parse_currency(form.min),
                                                    commishinfo.parse_currency(form.max),
                                                    form.currency,
                                                    30,)

        media.populate_with_user_media(results)
        return define.webpage(self.user_id, "etc/marketplace.html", [results, form])


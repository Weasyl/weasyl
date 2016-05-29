import itertools
import time

import web

from weasyl import define, index, macro, search, template, profile, siteupdate, submission
from weasyl.controllers.base import controller_base


# General browsing functions
class index_(controller_base):
    cache_name = "etc/index.html"

    def GET(self):
        now = time.time()
        page = define.common_page_start(self.user_id, options=["homepage"], title="Home")
        page.append(define.render(template.etc_index, index.template_fields(self.user_id)))
        return define.common_page_end(self.user_id, page, now=now)


class search_(controller_base):
    def GET(self):
        rating = define.get_rating(self.user_id)

        form = web.input(q="", find="", within="", rated=[], cat="", subcat="", backid="", nextid="")

        page = define.common_page_start(self.user_id, title="Browse and search")

        if form.q:
            find = form.find

            if find not in ("submit", "char", "journal", "user"):
                find = "submit"

            meta = {
                "q": form.q.strip(),
                "find": find,
                "within": form.within,
                "rated": set('gmap') & set(form.rated),
                "cat": int(form.cat) if form.cat else None,
                "subcat": int(form.subcat) if form.subcat else None,
                "backid": int(form.backid) if form.backid else None,
                "nextid": int(form.nextid) if form.nextid else None,
            }

            query, next_count, back_count = search.select(self.user_id, rating, limit=63, **meta)

            page.append(define.render("etc/search.html", [
                # Search method
                {"method": "search"},
                # Search metadata
                meta,
                # Search results
                query,
                next_count,
                back_count,
                # Submission subcategories
                macro.MACRO_SUBCAT_LIST,
            ]))
        elif form.find:
            query = search.browse(self.user_id, rating, 66, form)

            meta = {
                "find": form.find,
                "cat": int(form.cat) if form.cat else None,
            }

            page.append(define.render("etc/search.html", [
                # Search method
                {"method": "browse"},
                # Search metadata
                meta,
                # Search results
                query,
                0,
                0,
            ]))
        else:
            page.append(define.render("etc/search.html", [
                # Search method
                {"method": "summary"},
                # Search metadata
                None,
                # Search results
                {
                    "submit": search.browse(self.user_id, rating, 22, form, find="submit"),
                    "char": search.browse(self.user_id, rating, 22, form, find="char"),
                    "journal": search.browse(self.user_id, rating, 22, form, find="journal"),
                },
            ]))

        return define.common_page_end(self.user_id, page, rating, options={'search'})


# General browsing functions
class streaming_(controller_base):
    cache_name = "etc/streaming.html"

    def GET(self):
        extras = {
            "title": "Streaming",
        }
        rating = define.get_rating(self.user_id)
        return define.webpage(self.user_id, template.etc_streaming,
                              [profile.select_streaming(self.user_id, rating, 300, order_by="start_time desc")], **extras)


class site_update_(controller_base):
    def GET(self, updateid):
        updateid = int(updateid)

        return define.webpage(self.user_id, 'etc/site_update.html', [
            siteupdate.select_by_id(updateid),
        ])


class popular_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, 'etc/popular.html', [
            list(itertools.islice(
                index.filter_submissions(self.user_id, submission.select_recently_popular(), incidence_limit=1), 66))
        ])

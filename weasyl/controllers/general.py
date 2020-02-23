from __future__ import absolute_import

import itertools

from pyramid.view import view_config
from sqlalchemy.orm import joinedload

from libweasyl import ratings
from libweasyl.media import get_multi_user_media
from libweasyl.models.site import SiteUpdate

from weasyl import comment, define, index, macro, search, profile, submission


@view_config(route_name="index", renderer='/etc/index.jinja2')
def index_(request):
    return index.template_fields(request.userid)


@view_config(route_name="search", renderer='/etc/search.jinja2')
def search_(request):
    rating = define.get_rating(request.userid)

    form = request.web_input(q="", find="", within="", rated=[], cat="", subcat="", backid="", nextid="")

    if form.q:
        find = form.find

        if find not in ("submit", "char", "journal", "user"):
            find = "submit"

        q = form.q.strip()
        search_query = search.Query.parse(q, find)

        meta = {
            "q": q,
            "find": search_query.find,
            "within": form.within,
            "rated": set('gap') & set(form.rated),
            "cat": int(form.cat) if form.cat else None,
            "subcat": int(form.subcat) if form.subcat else None,
            "backid": int(form.backid) if form.backid else None,
            "nextid": int(form.nextid) if form.nextid else None,
        }

        if search_query.find == "user":
            query = search.select_users(q)
            next_count = back_count = 0
        else:
            search_query.ratings.update(ratings.CHARACTER_MAP[rating_code].code for rating_code in meta["rated"])

            query, next_count, back_count = search.select(
                userid=request.userid,
                rating=rating,
                limit=63,
                search=search_query,
                within=meta["within"],
                cat=meta["cat"],
                subcat=meta["subcat"],
                backid=meta["backid"],
                nextid=meta["nextid"])

        return {
            "options": {'search'},
            # Search method
            "method": {"method": "search"},
            # Search metadata
            "meta": meta,
            # Search results
            "results": query,
            "next_count": next_count,
            "back_count": back_count,
            # Submission subcategories
            "subcats": macro.MACRO_SUBCAT_LIST,
            "count_limit": search.COUNT_LIMIT
        }
    elif form.find:
        query = search.browse(request.userid, rating, 66, form)

        meta = {
            "find": form.find,
            "cat": int(form.cat) if form.cat else None,
        }

        return {
            "options": {'search'},
            # Search method
            "method": {"method": "browse"},
            # Search metadata
            "meta": meta,
            # Search results
            "results": query,
            "next_count": 0,
            "back_count": 0
        }
    else:
        return {
            "options": {'search'},
            # Search method
            "method": {"method": "summary"},
            # Search metadata
            "meta": None,
            # Search results
            "results": {
                "submit": search.browse(request.userid, rating, 22, form, find="submit"),
                "char": search.browse(request.userid, rating, 22, form, find="char"),
                "journal": search.browse(request.userid, rating, 22, form, find="journal"),
            }
        }


@view_config(route_name="streaming", renderer='/etc/streaming.jinja2')
def streaming_(request):
    rating = define.get_rating(request.userid)
    streaming = profile.select_streaming(request.userid, rating, 300, order_by="start_time desc")
    return {"streaming": streaming, "title": "Streaming"}


@view_config(route_name="site_update_list", renderer='/etc/site_update_list.jinja2')
def site_update_list_(request):
    updates = (
        SiteUpdate.query
        .order_by(SiteUpdate.updateid.desc())
        .options(joinedload('owner'))
        .all()
    )
    get_multi_user_media(*[update.userid for update in updates])

    return {"updates": updates, "title": "Site Updates"}


@view_config(route_name="site_update", renderer='/etc/site_update.jinja2')
def site_update_(request):
    updateid = int(request.matchdict['update_id'])
    update = SiteUpdate.query.get_or_404(updateid)
    myself = profile.select_myself(request.userid)
    comments = comment.select(request.userid, updateid=updateid)

    return {"myself": myself, "update": update, "comments": comments, "title": "Site Update"}


@view_config(route_name="popular", renderer='/etc/popular.jinja2')
def popular_(request):
    popular = list(
        itertools.islice(
            index.filter_submissions(request.userid, submission.select_recently_popular(), incidence_limit=1),
            66
        )
    )
    return {"submissions": popular, "title": "Recently Popular"}

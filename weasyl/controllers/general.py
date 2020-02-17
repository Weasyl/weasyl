from __future__ import absolute_import

import itertools

from pyramid.response import Response
from sqlalchemy.orm import joinedload

from libweasyl import ratings
from libweasyl import staff
from libweasyl.media import get_multi_user_media
from libweasyl.models.site import SiteUpdate

from weasyl import comment, define, index, macro, search, profile, submission


# General browsing functions
def index_(request):
    page = define.common_page_start(request.userid, title="Home")
    page.append(define.render("etc/index.html", index.template_fields(request.userid)))
    return Response(define.common_page_end(request.userid, page))


def search_(request):
    rating = define.get_rating(request.userid)

    q = request.params.get('q', None)
    find = request.params.get('find', None)
    within = request.params.get('within', '')
    rated = request.params.get('rated')
    cat = request.params.get('cat', None)
    subcat = request.params.get('subcat', None)
    backid = request.params.get('backid', None)
    nextid = request.params.get('nextid', None)

    page = define.common_page_start(request.userid, title="Browse and search")

    if q:
        if find not in ("submit", "char", "journal", "user"):
            find = "submit"

        q = q.strip()
        search_query = search.Query.parse(q, find)

        meta = {
            "q": q,
            "find": search_query.find,
            "within": within,
            "rated": set('gap') & set(rated),
            "cat": int(cat) if cat else None,
            "subcat": int(subcat) if subcat else None,
            "backid": int(backid) if backid else None,
            "nextid": int(nextid) if nextid else None,
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
            search.COUNT_LIMIT,
        ]))
    elif find:
        query = search.browse(request.userid, rating, 66, find, cat, backid, nextid)

        meta = {
            "find": find,
            "cat": int(cat) if cat else None,
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
                "submit": search.browse(request.userid, rating, 22, "submit", cat, backid, nextid),
                "char": search.browse(request.userid, rating, 22, "char", cat, backid, nextid),
                "journal": search.browse(request.userid, rating, 22, "journal", cat, backid, nextid),
            },
        ]))

    return Response(define.common_page_end(request.userid, page, options={'search'}))


def streaming_(request):
    rating = define.get_rating(request.userid)
    return Response(define.webpage(request.userid, 'etc/streaming.html',
                                   (profile.select_streaming(request.userid, rating, 300, order_by="start_time desc"),),
                                   title="Streaming"))


def site_update_list_(request):
    updates = (
        SiteUpdate.query
        .order_by(SiteUpdate.updateid.desc())
        .options(joinedload('owner'))
        .all()
    )
    get_multi_user_media(*[update.userid for update in updates])

    can_edit = request.userid in staff.ADMINS

    return Response(define.webpage(request.userid, 'etc/site_update_list.html', (request, updates, can_edit), title="Site Updates"))


def site_update_(request):
    updateid = int(request.matchdict['update_id'])
    update = SiteUpdate.query.get_or_404(updateid)
    myself = profile.select_myself(request.userid)
    comments = comment.select(request.userid, updateid=updateid)

    return Response(define.webpage(request.userid, 'etc/site_update.html', (myself, update, comments), title="Site Update"))


def popular_(request):
    return Response(define.webpage(request.userid, 'etc/popular.html', [
        list(itertools.islice(
            index.filter_submissions(request.userid, submission.select_recently_popular(), incidence_limit=1), 66))
    ], title="Recently Popular"))

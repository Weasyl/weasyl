import itertools
import time

from pyramid.response import Response

from libweasyl import ratings

from weasyl import define, index, macro, search, profile, siteupdate, submission


# General browsing functions
def index_(request):
    now = time.time()
    page = define.common_page_start(request.userid, options=["homepage"], title="Home")
    page.append(define.render("etc/index.html", index.template_fields(request.userid)))
    return Response(define.common_page_end(request.userid, page, now=now))


def search_(request):
    rating = define.get_rating(request.userid)

    form = request.web_input(q="", find="", within="", rated=[], cat="", subcat="", backid="", nextid="")

    page = define.common_page_start(request.userid, title="Browse and search")

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

        search_query = search.Query.parse(meta["q"], find)

        if search_query.find == "user":
            query = search.select_users(meta["q"])
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
    elif form.find:
        query = search.browse(request.userid, rating, 66, form)

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
                "submit": search.browse(request.userid, rating, 22, form, find="submit"),
                "char": search.browse(request.userid, rating, 22, form, find="char"),
                "journal": search.browse(request.userid, rating, 22, form, find="journal"),
            },
        ]))

    return Response(define.common_page_end(request.userid, page, rating, options={'search'}))


def streaming_(request):
    extras = {
        "title": "Streaming",
    }
    rating = define.get_rating(request.userid)
    return Response(define.webpage(request.userid, 'etc/streaming.html',
                                   [profile.select_streaming(request.userid, rating, 300, order_by="start_time desc")],
                                   **extras))


def site_update_(request):
    updateid = int(request.matchdict['update_id'])

    return Response(define.webpage(request.userid, 'etc/site_update.html', [
        siteupdate.select_by_id(updateid),
    ]))


def popular_(request):
    return Response(define.webpage(request.userid, 'etc/popular.html', [
        list(itertools.islice(
            index.filter_submissions(request.userid, submission.select_recently_popular(), incidence_limit=1), 66))
    ]))

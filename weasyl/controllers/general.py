import itertools

from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response

from libweasyl import ratings

from weasyl import define, index, macro, search, profile, submission


# General browsing functions
def index_(request):
    page = define.common_page_start(request.userid, title="Home", canonical_url="/")
    page.append(define.render("etc/index.html", index.template_fields(request.userid)))

    if request.userid == 0:
        cache_control = "public, max-age=60, stale-while-revalidate=600"
    else:
        cache_control = "private, max-age=60"

    return Response(
        define.common_page_end(request.userid, page, options=("index",)),
        cache_control=cache_control,
        vary=["Cookie"],  # SFW mode, sign in/out, account changes
    )


_BROWSE = {
    'submit': ("Submissions", "Browse Submissions"),
    'char': ("Characters", "Browse Characters"),
    'journal': ("Journals", "Browse Journals"),
    'critique': ("Critique requests", "Browse Critique Requests"),
}


def search_(request):
    rating = define.get_rating(request.userid)

    q = request.params.get('q')
    find = request.params.get('find')
    within = request.params.get('within', '')
    rated = request.params.getall('rated')
    cat = request.params.get('cat')
    subcat = request.params.get('subcat')
    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

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
            prev_page = next_page = None
        else:
            search_query.ratings.update(ratings.CHARACTER_MAP[rating_code].code for rating_code in meta["rated"])

            if backid:
                page = search.PrevFilter(meta["backid"])
            elif nextid:
                page = search.NextFilter(meta["nextid"])
            else:
                page = search.FIRST_PAGE

            query, prev_page, next_page = search.select(
                userid=request.userid,
                rating=rating,
                limit=63,
                search=search_query,
                within=meta["within"],
                cat=meta["cat"],
                subcat=meta["subcat"],
                page=page,
            )

        title = "Search results"
        template_args = (
            # Search method
            "search",
            # Search metadata
            meta,
            # Search results
            query,
            prev_page,
            next_page,
            # Submission subcategories
            macro.MACRO_SUBCAT_LIST,
            # `browse_header`
            None,
            # `is_guest`
            not request.userid,
            # `rating_limit`
            rating,
        )
    elif find:
        if find not in ("submit", "char", "journal", "critique"):
            raise HTTPNotFound()

        query = search.browse(
            userid=request.userid,
            rating=rating,
            limit=66,
            find=find,
            cat=cat,
            backid=define.get_int(backid),
            nextid=define.get_int(nextid),
        )

        meta = {
            "find": find,
            "cat": int(cat) if cat else None,
        }

        title, browse_header = _BROWSE[find]
        template_args = (
            # Search method
            "browse",
            # Search metadata
            meta,
            # Search results
            query,
            # `prev_page`
            None,
            # `next_page`
            None,
            # `subcats`
            None,
            browse_header,
        )
    else:
        title = "Browse"
        template_args = (
            # Search method
            "summary",
            # Search metadata
            None,
            # Search results
            {
                "submit": search.browse(
                    userid=request.userid,
                    rating=rating,
                    limit=22,
                    find="submit",
                    cat=None,
                    backid=None,
                    nextid=None,
                ),
                "char": search.browse(
                    userid=request.userid,
                    rating=rating,
                    limit=22,
                    find="char",
                    cat=None,
                    backid=None,
                    nextid=None,
                ),
                "journal": search.browse(
                    userid=request.userid,
                    rating=rating,
                    limit=22,
                    find="journal",
                    cat=None,
                    backid=None,
                    nextid=None,
                ),
            },
        )

    return Response(define.webpage(request.userid, "etc/search.html", template_args, options=('search',), title=title))


def streaming_(request):
    return Response(define.webpage(request.userid, 'etc/streaming.html',
                                   (profile.select_streaming(request.userid),),
                                   title="Streaming"))


def popular_(request):
    return Response(define.webpage(request.userid, 'etc/popular.html', [
        list(itertools.islice(
            index.filter_submissions(request.userid, submission.select_recently_popular(), incidence_limit=1), 66))
    ], title="Recently Popular"))

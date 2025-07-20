import itertools
from typing import Literal

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


_SEARCH_RESULTS = {
    "submit": "Posts",
    "char": "Characters",
    "journal": "Journals",
}


_BROWSE = {
    'submit': ("Submissions", "Browse Submissions"),
    'char': ("Characters", "Browse Characters"),
    'journal': ("Journals", "Browse Journals"),
    'critique': ("Critique requests", "Browse Critique Requests"),
}


# NOTE: Most canonical paths are good candidates for a `history.replaceState`, but ones that include freeform user input (like this one) are exceptions: it would be annoying to the user to process and rearrange the input if they want to continue making changes to it, especially in cases where the original input was slightly wrong in a way that dramatically changed its interpretation. TODO: Consider a similar function for the purpose of `replaceState`-style use cases, leaving the form state intact while removing defaults. TODO: Display the interpretation of the query.
def _get_search_canonical_path(
    search_query: search.Query,
    *,
    within: Literal["", "notify", "fave", "friend", "follow"],
    cat: int | None,
    subcat: int | None,
    backid: int | None,
    nextid: int | None,
) -> str:
    params = {
        "q": search_query.get_terms_string(),
    }

    find = search_query.find

    if find != "submit":
        params["find"] = find

    if find != "user" and within:
        params["within"] = within

    if find != "user" and ratings:
        params["rated"] = [ratings.CODE_MAP[r].character for r in sorted(search_query.ratings)]

    if find == "submit":
        if subcat:
            params["subcat"] = str(subcat)
        elif cat:
            params["cat"] = str(cat)

    if find != "user":
        if backid:
            params["backid"] = str(backid)
        elif nextid:
            params["nextid"] = str(nextid)

    return f"/search?{define.query_string(params)}"


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

    canonical_path = None
    robots = None

    if q:
        if find not in ("submit", "char", "journal", "user"):
            find = "submit"

        if (
            not request.userid
            or within not in ["", "notify", "fave", "friend", "follow"]
        ):
            within = ""

        if find != "submit":
            cat = subcat = None

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
            if len(search_query.ratings) == len(ratings.ALL_RATINGS):
                search_query.ratings.clear()

            resolved = search.resolve(search_query)
            if resolved is None:
                query, prev_page, next_page = [], None, None
            else:
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
                    resolved=resolved,
                    within=within,
                    cat=meta["cat"],
                    subcat=meta["subcat"],
                    page=page,
                )

        if (
            search_query.find != "user"
            and not within
            and not cat
            and not subcat
            and (simple := search_query.as_simple())
        ):
            title = f'{_SEARCH_RESULTS[search_query.find]} tagged “{simple}”'

            # Don’t index reverse pagination or empty result sets.
            if backid or not query:
                robots = "noindex"
        else:
            title = "Search results"
            robots = "noindex"

        canonical_path = _get_search_canonical_path(
            search_query,
            within=meta["within"],
            cat=meta["cat"],
            subcat=meta["subcat"],
            backid=meta["backid"],
            nextid=meta["nextid"],
        )

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
                    # TODO: revisit limit once characters get a different thumbnail layout; currently, 14 is the most that can fit
                    limit=14,
                    find="char",
                    cat=None,
                    backid=None,
                    nextid=None,
                ),
                "journal": search.browse(
                    userid=request.userid,
                    rating=rating,
                    limit=12,
                    find="journal",
                    cat=None,
                    backid=None,
                    nextid=None,
                ),
            },
        )

    return Response(
        define.webpage(
            request.userid,
            "etc/search.html",
            template_args,
            options=('search',),
            title=title,
            canonical_url=canonical_path,
            robots=robots,
        )
    )


def streaming_(request):
    return Response(define.webpage(request.userid, 'etc/streaming.html',
                                   (profile.select_streaming(request.userid),),
                                   title="Streaming"))


def popular_(request):
    card_viewer = define.get_card_viewer()
    return Response(define.webpage(request.userid, 'etc/popular.html', [
        card_viewer.get_cards(itertools.islice(
            index.filter_submissions(request.userid, submission.select_recently_popular(), incidence_limit=1), 66))
    ], title="Recently Popular"))

from pyramid.response import Response

from libweasyl import ratings
from weasyl import define, search
from weasyl.forms import expect_id
from weasyl.search import NextFilter
from weasyl.search import PrevFilter


RESULTS_PER_PAGE = 63


def navigation_counts(request):
    if not (find := request.GET.get('find')):
        find = 'submit'
    query = search.Query.parse(request.GET.get('q'), find)
    query.ratings.update(ratings.CHARACTER_MAP[rating_code].code for rating_code in set('gap') & set(request.GET.getall('rated')))

    cat = request.GET.get('cat')
    subcat = request.GET.get('subcat')
    backid = request.GET.get('backid')
    nextid = request.GET.get('nextid')

    resolved = search.resolve(query)
    if resolved is None:
        return Response(json={
            'nextCount': 0,
            'backCount': 0,
        })

    def _search(page: PrevFilter | NextFilter) -> int:
        return search.select_count(
            userid=request.userid,
            rating=define.get_rating(request.userid),
            resolved=resolved,
            within=request.GET.get('within', ''),
            cat=int(cat) if cat else None,
            subcat=int(subcat) if subcat else None,
            page=page,
        )

    back_count = None if backid is None else _search(PrevFilter(expect_id(backid)))
    next_count = None if nextid is None else _search(NextFilter(expect_id(nextid)))

    counts = {
        'nextCount': next_count,
        'backCount': back_count,
    }

    return Response(json=counts)

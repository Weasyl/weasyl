from pyramid.response import Response

from libweasyl import ratings
from weasyl import define, search


def navigation_counts(request):
    if not (find := request.GET.get('find')):
        find = 'submit'
    query = search.Query.parse(request.GET.get('q'), find)
    query.ratings.update(ratings.CHARACTER_MAP[rating_code].code for rating_code in set('gap') & set(request.GET.getall('rated')))

    cat = request.GET.get('cat')
    subcat = request.GET.get('subcat')
    backid = request.GET.get('backid')
    nextid = request.GET.get('nextid')

    _, next_count, back_count = search._find_without_media(
        userid=request.userid,
        rating=define.get_rating(request.userid),
        limit=63,
        search=query,
        within=request.GET.get('within', ''),
        cat=int(cat) if cat else None,
        subcat=int(subcat) if subcat else None,
        backid=int(backid) if backid else None,
        nextid=int(nextid) if nextid else None,
        get_counts=True,
    )

    counts = {
        'nextCount': next_count,
        'backCount': back_count,
    }

    return Response(json=counts)

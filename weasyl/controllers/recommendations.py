from pyramid.response import Response

from weasyl import define as d
from weasyl.controllers.decorators import login_required
from weasyl.recommendation import select_list


@login_required
def recommendations_list_(request):
    # TODO(hyena): This will return roughly 100 items. We don't need that many so cut them off.
    # TODO(hyena): Handle the case where this returns none due to no favorites.
    recs = select_list(userid=request.userid, rating=d.get_rating(request.userid))

    page = d.common_page_start(request.userid, options=["recommendations"], title="Recommendations")
    page.append(d.render("recommendation/recommendations.html", [recs]))
    return Response(d.common_page_end(request.userid, page))
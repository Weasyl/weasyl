from pyramid.response import Response

from weasyl.controllers.decorators import login_required
from weasyl.recommendation import recs_for_user


@login_required
def recommendations_list_(request):
    return Response("\n".join(str(x) for x in recs_for_user(request.userid)))
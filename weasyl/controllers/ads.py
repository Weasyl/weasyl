from __future__ import absolute_import, division, unicode_literals

from datetime import datetime
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import ads
from weasyl import define
from weasyl.controllers.decorators import moderator_only, token_checked
from weasyl.error import WeasylError


@moderator_only
def create_form_(request):
    return Response(define.render("ads/create.html", (None,)))


@moderator_only
@token_checked
def create_(request):
    form = request.web_input(image="", owner="", end="")

    try:
        form.end = datetime.strptime(form.end, "%Y-%m-%d")
    except ValueError:
        raise WeasylError("adEndDateInvalid")

    ad_id = ads.create_ad(form)

    return Response(define.render("ads/create.html", (
        ad_id,
    )))


def list_(request):
    return Response(define.webpage(request.userid, "ads/list.html", (
        request.userid,
        ads.get_current_ads(),
    )))


@moderator_only
@token_checked
def takedown_(request):
    form = request.web_input(takedown="")

    ad_id = int(form.takedown)
    ads.expire(ad_id)

    raise HTTPSeeOther(location="/ads")

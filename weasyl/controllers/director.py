from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define as d
from weasyl import searchtag
from weasyl.controllers.decorators import director_only
from weasyl.controllers.decorators import token_checked

""" Director control panel view callables """


@director_only
def directorcontrol_(request):
    return Response(d.webpage(request.userid, "directorcontrol/directorcontrol.html", title="Director Control Panel"))


@director_only
def directorcontrol_globaltagrestrictions_get_(request):
    tags = searchtag.get_global_tag_restrictions()
    return Response(d.webpage(request.userid, "directorcontrol/globaltagrestrictions.html", (
        tags,
    ), title="Edit Global Community Tagging Restrictions"))


@director_only
@token_checked
def directorcontrol_globaltagrestrictions_post_(request):
    tags = searchtag.parse_restricted_tags(request.params["tags"])
    searchtag.edit_global_tag_restrictions(request.userid, tags)
    raise HTTPSeeOther(location="/directorcontrol/globaltagrestrictions")

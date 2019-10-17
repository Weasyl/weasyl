

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
def directorcontrol_emailblacklist_get_(request):
    query = d.engine.execute("""
        SELECT id, domain_name, added_by, reason, lo.login_name AS name
        FROM emailblacklist
        INNER JOIN login AS lo ON added_by = lo.userid
        ORDER BY domain_name
    """)
    blacklist_information = list(map(dict, query))
    return Response(d.webpage(request.userid, "directorcontrol/emailblacklist.html", [blacklist_information],
                              title="Edit Account Creation Email Blacklist"))


@token_checked
@director_only
def directorcontrol_emailblacklist_post_(request):
    form = request.web_input(action=None, remove_selection=[], domain_name=None, reason=None)
    # Remove entr(y|ies) from blacklist
    if form.action == "remove":
        d.engine.execute("DELETE FROM emailblacklist WHERE id = ANY (%(selected_ids)s)",
                         selected_ids=list(map(int, form.remove_selection)))

    # Add any entries to blacklist, if any in form.domain_name; duplicate entries are silently discarded.
    elif form.action == "add" and form.domain_name:
        d.engine.execute("""
            INSERT INTO emailblacklist (domain_name, reason, added_by)
                SELECT UNNEST(%(domain_name)s), %(reason)s, %(added_by)s
            ON CONFLICT (domain_name) DO NOTHING
        """, domain_name=form.domain_name.split(), reason=form.reason, added_by=request.userid)

    raise HTTPSeeOther(location="/directorcontrol/emailblacklist")


@director_only
def directorcontrol_globaltagrestrictions_get_(request):
    tags = searchtag.get_global_tag_restrictions(request.userid)
    return Response(d.webpage(request.userid, "directorcontrol/globaltagrestrictions.html", (
        tags,
    ), title="Edit Global Community Tagging Restrictions"))


@director_only
@token_checked
def directorcontrol_globaltagrestrictions_post_(request):
    tags = searchtag.parse_restricted_tags(request.params["tags"])
    searchtag.edit_global_tag_restrictions(request.userid, tags)
    raise HTTPSeeOther(location="/directorcontrol/globaltagrestrictions")

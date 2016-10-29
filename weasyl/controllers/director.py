from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl.controllers.decorators import director_only
from weasyl.controllers.decorators import token_checked
from weasyl import define as d


""" Director control panel view callables """


@director_only
def directorcontrol_(request):
    return Response(d.webpage(request.userid, "directorcontrol/directorcontrol.html"))


@director_only
def directorcontrol_emailblacklist_get_(request):
    query = d.engine.execute("""
        SELECT id, domain_name, added_by, reason, lo.login_name AS name
        FROM emailblacklist
        INNER JOIN login AS lo ON added_by = lo.userid
        ORDER BY domain_name
    """)
    blacklist_information = map(dict, query)
    return Response(d.webpage(request.userid, "directorcontrol/emailblacklist.html", [blacklist_information]))


@token_checked
@director_only
def directorcontrol_emailblacklist_post_(request):
    form = request.web_input(action=None, remove_selection=[], domain_name=None, reason=None)
    # Remove entr(y|ies) from blacklist
    if form.action == "remove":
        d.engine.execute("DELETE FROM emailblacklist WHERE id = ANY (%(selected_ids)s)",
                         selected_ids=map(int, form.remove_selection))

    # Add entry to blacklist
    elif form.action == "add" and form.domain_name:
        if len(form.domain_name) <= 252:
            d.engine.execute("""
                INSERT INTO emailblacklist (domain_name, reason, added_by)
                    VALUES (%(domain_name)s, %(reason)s, %(added_by)s)
                    ON CONFLICT (domain_name) DO NOTHING
            """, domain_name=form.domain_name.lower(), reason=form.reason, added_by=request.userid)

    raise HTTPSeeOther(location="/directorcontrol/emailblacklist")

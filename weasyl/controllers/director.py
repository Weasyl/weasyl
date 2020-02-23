from __future__ import absolute_import

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from weasyl import define as d
from weasyl import searchtag
from weasyl.controllers.decorators import director_only
from weasyl.controllers.decorators import token_checked

""" Director control panel view callables """


@view_config(route_name="directorcontrol", renderer='/directorcontrol/directorcontrol.jinja2')
@director_only
def directorcontrol_(request):
    return {'title': "Director Control Panel"}


@view_config(route_name="directorcontrol_emailblacklist", renderer='/directorcontrol/emailblacklist.jinja2', request_method="GET")
@director_only
def directorcontrol_emailblacklist_get_(request):
    query = d.engine.execute("""
        SELECT id, domain_name, added_by, reason, lo.login_name AS name
        FROM emailblacklist
        INNER JOIN login AS lo ON added_by = lo.userid
        ORDER BY domain_name
    """)
    blacklist_information = map(dict, query)
    return {'entries': blacklist_information, 'title': "Edit Account Creation Email Blacklist"}


@view_config(route_name="directorcontrol_emailblacklist", renderer='/directorcontrol/emailblacklist.jinja2', request_method="POST")
@token_checked
@director_only
def directorcontrol_emailblacklist_post_(request):
    form = request.web_input(action=None, remove_selection=[], domain_name=None, reason=None)
    # Remove entr(y|ies) from blacklist
    if form.action == "remove":
        d.engine.execute("DELETE FROM emailblacklist WHERE id = ANY (%(selected_ids)s)",
                         selected_ids=map(int, form.remove_selection))

    # Add any entries to blacklist, if any in form.domain_name; duplicate entries are silently discarded.
    elif form.action == "add" and form.domain_name:
        d.engine.execute("""
            INSERT INTO emailblacklist (domain_name, reason, added_by)
                SELECT UNNEST(%(domain_name)s), %(reason)s, %(added_by)s
            ON CONFLICT (domain_name) DO NOTHING
        """, domain_name=form.domain_name.split(), reason=form.reason, added_by=request.userid)

    raise HTTPSeeOther(location="/directorcontrol/emailblacklist")


@view_config(route_name="directorcontrol_globaltagrestrictions", renderer='/directorcontrol/globaltagrestrictions.jinja2', request_method="GET")
@director_only
def directorcontrol_globaltagrestrictions_get_(request):
    tags = searchtag.get_global_tag_restrictions(request.userid)
    return {'tags': tags, 'title': "Edit Global Community Tagging Restrictions"}


@view_config(route_name="directorcontrol_globaltagrestrictions", renderer='/directorcontrol/globaltagrestrictions.jinja2', request_method="POST")
@director_only
@token_checked
def directorcontrol_globaltagrestrictions_post_(request):
    tags = searchtag.parse_restricted_tags(request.params["tags"])
    searchtag.edit_global_tag_restrictions(request.userid, tags)
    raise HTTPSeeOther(location="/directorcontrol/globaltagrestrictions")

from __future__ import absolute_import

from pyramid.view import view_config

from libweasyl import staff

from weasyl.controllers.decorators import login_required
from weasyl import define, profile, report


# Policy functions
@view_config(route_name="staff", renderer='/help/staff.jinja2')
def staff_(request):
    directors = staff.DIRECTORS
    technical = staff.TECHNICAL - staff.DIRECTORS
    admins = staff.ADMINS - staff.DIRECTORS - staff.TECHNICAL
    mods = staff.MODS - staff.ADMINS
    devs = staff.DEVELOPERS
    staff_info_map = profile.select_avatars(list(directors | technical | admins | mods | devs))
    staff_list = []
    for name, userids in [('Directors', directors),
                          ('Administrators', admins),
                          ('Moderators', mods),
                          ('Techs', technical),
                          ('Developers', devs)]:
        users = [staff_info_map[u] for u in userids]
        users.sort(key=lambda info: info['username'].lower())
        staff_list.append((name, users))

    return {'staff': staff_list, 'title': "Staff"}


@view_config(route_name="thanks", renderer='/help/thanks.jinja2')
def thanks_(request):
    return {'title': "Awesome People"}


@view_config(route_name="policy_community", renderer='/help/community.jinja2')
def policy_community_(request):
    return {'title': "Community Guidelines"}


@view_config(route_name="policy_copyright", renderer='/help/copyright.jinja2')
def policy_copyright_(request):
    return {'title': "Copyright Policy"}


@view_config(route_name="policy_privacy", renderer='/help/privacy.jinja2')
def policy_privacy_(request):
    return {'title': "Privacy Policy"}


@view_config(route_name="policy_scoc", renderer='/help/scoc.jinja2')
def policy_scoc_(request):
    return {'title': 'Staff Code of Conduct'}


@view_config(route_name="policy_tos", renderer='/help/tos.jinja2')
def policy_tos_(request):
    return {'title': 'Terms of Service'}


# Help functions
@view_config(route_name="help", renderer='/help/help.jinja2')
def help_(request):
    return {'title': 'Help Topics'}


@view_config(route_name="help_about", renderer='/help/about.jinja2')
def help_about_(request):
    return {'title': 'About Weasyl'}


@view_config(route_name="help_collections", renderer='/help/collections.jinja2')
def help_collections_(request):
    return {'title': 'Collections'}


@view_config(route_name="help_faq", renderer='/help/faq.jinja2')
def help_faq_(request):
    return {'title': 'FAQ'}


@view_config(route_name="help_folders", renderer='/help/folder-options.jinja2')
def help_folders_(request):
    return {'title': 'Folder Options'}


@view_config(route_name="help_gdocs", renderer='/help/gdocs.jinja2')
def help_gdocs_(request):
    return {'title': 'Google Drive Embedding'}


@view_config(route_name="help_markdown", renderer='/help/markdown.jinja2')
def help_markdown_(request):
    return {'title': 'Markdown'}


@view_config(route_name="help_marketplace", renderer='/help/marketplace.jinja2')
def help_marketplace_(request):
    return {'title': 'Marketplace'}


@view_config(route_name="help_ratings", renderer='/help/ratings.jinja2')
def help_ratings_(request):
    return {'title': 'Content Ratings'}


@view_config(route_name="help_reports", renderer='/help/reports.jinja2')
@login_required
def help_reports_(request):
    return {
        'reports': report.select_reported_list(request.userid),
        'title': "My Reports"
    }


@view_config(route_name="help_searching", renderer='/help/searching.jinja2')
def help_searching_(request):
    return {'title': 'Searching'}


@view_config(route_name="help_tagging", renderer='/help/tagging.jinja2')
def help_tagging_(request):
    return {'title': 'Tagging'}


@view_config(route_name="help_two_factor_authentication", renderer='/help/two_factor_authentication.jinja2')
def help_two_factor_authentication_(request):
    return {'title': 'Two-Factor Authentication'}


@view_config(route_name="help_verification", renderer='/help/verification.jinja2')
def help_verification_(request):
    username = define.get_display_name(request.userid)

    return {'username': username, 'title': "Account Verification"}

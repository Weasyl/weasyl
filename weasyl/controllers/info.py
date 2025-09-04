from pyramid.response import Response

from libweasyl import staff

from weasyl.controllers.decorators import login_required
from weasyl import define, profile, report


def _help_page(template, *, title):
    def respond(request):
        return Response(define.webpage(request.userid, template, options=("help",), title=title))

    return respond


# Policy functions

def staff_(request):
    directors = staff.DIRECTORS
    admins = staff.ADMINS - staff.DIRECTORS
    mods = staff.MODS - staff.ADMINS
    devs = staff.DEVELOPERS
    staff_info_map = profile.select_avatars(list(directors | admins | mods | devs))
    staff_list = []
    for name, userids in [('Directors', directors),
                          ('Administrators', admins),
                          ('Moderators', mods),
                          ('Developers', devs)]:
        users = [staff_info_map[u] for u in userids]
        users.sort(key=lambda info: info['username'].lower())
        staff_list.append((name, users))

    return Response(define.webpage(request.userid, "help/staff.html", [staff_list],
                                   title="Staff"))


thanks_ = _help_page("help/thanks.html", title="Awesome People")

policy_community_ = _help_page("help/community.html", title="Community Guidelines")
policy_copyright_ = _help_page("help/copyright.html", title="Copyright Policy")
policy_privacy_ = _help_page("help/privacy.html", title="Privacy Policy")
policy_scoc_ = _help_page("help/scoc.html", title="Staff Code of Conduct")
policy_tos_ = _help_page("help/tos.html", title="Terms of Service")

help_ = _help_page("help/help.html", title="Help Topics")
help_about_ = _help_page("help/about.html", title="About Weasyl")
help_collections_ = _help_page("help/collections.html", title="Collections")
help_faq_ = _help_page("help/faq.html", title="FAQ")
help_folders_ = _help_page("help/folder-options.html", title="Folder Options")
help_gdocs_ = _help_page("help/gdocs.html", title="Google Docs Embedding")
help_markdown_ = _help_page("help/markdown.html", title="Markdown")
help_marketplace_ = _help_page("help/marketplace.html", title="Marketplace")
help_ratings_ = _help_page("help/ratings.html", title="Content Ratings")
help_searching_ = _help_page("help/searching.html", title="Searching")
help_tagging_ = _help_page("help/tagging.html", title="Tagging")
help_two_factor_authentication_ = _help_page("help/two_factor_authentication.html", title="Two-Factor Authentication")


@login_required
def help_reports_(request):
    return Response(define.webpage(request.userid, "help/reports.html", [
        report.select_reported_list(request.userid),
    ], title="My Reports"))


def help_verification_(request):
    username = define.get_username(request.userid) if request.userid else None

    return Response(define.webpage(request.userid, "help/verification.html", [username],
                                   options=("help",),
                                   title="Account Verification"))

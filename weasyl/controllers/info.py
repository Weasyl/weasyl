from __future__ import absolute_import

from pyramid.response import Response

from libweasyl import staff

from weasyl.controllers.decorators import login_required
from weasyl import define, profile, report


# Policy functions

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

    return Response(define.webpage(request.userid, "help/staff.html", [staff_list],
                                   title="Staff"))


def thanks_(request):
    return Response(define.webpage(request.userid, "help/thanks.html",
                                   title="Awesome People"))


def policy_community_(request):
    return Response(define.webpage(request.userid, "help/community.html",
                                   title="Community Guidelines"))


def policy_community_changes_(request):
    return Response(define.webpage(request.userid, "help/community-changes.html",
                                   title="Community Guidelines"))


def policy_copyright_(request):
    return Response(define.webpage(request.userid, "help/copyright.html",
                                   title="Copyright Policy"))


def policy_privacy_(request):
    return Response(define.webpage(request.userid, "help/privacy.html",
                                   title="Privacy Policy"))


def policy_scoc_(request):
    return Response(define.webpage(request.userid, "help/scoc.html",
                                   title="Staff Code of Conduct"))


def policy_tos_(request):
    return Response(define.webpage(request.userid, "help/tos.html",
                                   title="Terms of Service"))


# Help functions
def help_(request):
    return Response(define.webpage(request.userid, "help/help.html",
                                   title="Help Topics"))


def help_about_(request):
    return Response(define.webpage(request.userid, "help/about.html",
                                   title="About Weasyl"))


def help_collections_(request):
    return Response(define.webpage(request.userid, "help/collections.html",
                                   title="Collections"))


def help_faq_(request):
    return Response(define.webpage(request.userid, "help/faq.html",
                                   title="FAQ"))


def help_folders_(request):
    return Response(define.webpage(request.userid, "help/folder-options.html",
                                   title="Folder Options"))


def help_gdocs_(request):
    return Response(define.webpage(request.userid, "help/gdocs.html",
                                   title="Google Drive Embedding"))


def help_markdown_(request):
    return Response(define.webpage(request.userid, "help/markdown.html",
                                   title="Markdown"))


def help_marketplace_(request):
    return Response(define.webpage(request.userid, "help/marketplace.html",
                                   title="Marketplace"))


def help_ratings_(request):
    return Response(define.webpage(request.userid, "help/ratings.html",
                                   title="Content Ratings"))


def help_ratings_changes_(request):
    return Response(define.webpage(request.userid, "help/ratings-changes.html",
                                   title="Content Ratings"))


@login_required
def help_reports_(request):
    return Response(define.webpage(request.userid, "help/reports.html", [
        report.select_reported_list(request.userid),
    ]))


def help_searching_(request):
    return Response(define.webpage(request.userid, "help/searching.html",
                                   title="Searching"))


def help_tagging_(request):
    return Response(define.webpage(request.userid, "help/tagging.html",
                                   title="Tagging"))


def help_two_factor_authentication_(request):
    return Response(define.webpage(request.userid, "help/two_factor_authentication.html",
                                   title="Two-Factor Authentication"))

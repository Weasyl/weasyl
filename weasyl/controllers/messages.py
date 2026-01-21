from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define, message
from weasyl.controllers.decorators import login_required, token_checked

"""Contains view callables dealing with notification messages."""


@login_required
@token_checked
def messages_remove_(request):
    remove_all_before = request.POST.get('remove-all-before')

    if remove_all_before:
        message.remove_all_before(request.userid, int(remove_all_before))
    elif 'remove-all-submissions' in request.POST:
        message.remove_all_submissions(request.userid, int(request.POST['remove-all-submissions']))
    else:
        remove = list(map(int, request.POST.getall('remove')))
        message.remove(request.userid, remove)

    if 'recall' in request.POST:
        raise HTTPSeeOther(location="/messages/submissions")
    else:
        raise HTTPSeeOther(location="/messages/notifications")


@login_required
def messages_notifications_(request):
    sections = [
        (message.cluster(section_notifications), section_id)
        for section_notifications, section_id in [
            (message.select_comments(request.userid), 'comments'),
            (message.select_notifications(request.userid), 'notifications'),
            (message.select_journals(request.userid), None),
        ]
        if section_notifications
    ]

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/notifications.html", (
        sections,
    ), title='Notifications'))


@login_required
def messages_submissions_(request):
    backtime = request.GET.get('backtime')
    nexttime = request.GET.get('nexttime')

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/submissions_thumbnails.html", (
        # Submissions
        message.select_submissions(
            request.userid,
            limit=66,
            include_tags=False,
            backtime=define.get_int(backtime),
            nexttime=define.get_int(nexttime),
        ),
    ), title='Submission Notifications'))

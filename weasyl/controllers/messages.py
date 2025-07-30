import itertools

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


def tag_section(results, section):
    for row in results:
        row['section'] = section
    return results


def sort_notifications(notifications):
    return [
        row
        for key, group in itertools.groupby(
            notifications, lambda row: message.notification_clusters.get(row['type']))
        for row in sorted(group, key=lambda row: row['unixtime'], reverse=True)
    ]


@login_required
def messages_notifications_(request):
    """ todo finish listing of message types in the template """

    notifications = (
        tag_section(message.select_comments(request.userid), 'comments') +
        tag_section(message.select_notifications(request.userid), 'notifications') +
        tag_section(message.select_journals(request.userid), 'journals')
    )

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/notifications.html", [
        sort_notifications(notifications),
    ], title='Notifications'))


@login_required
def messages_submissions_(request):
    backtime = request.GET.get('backtime')
    nexttime = request.GET.get('nexttime')

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/submissions_thumbnails.html", (
        # Submissions
        message.select_submissions(request.userid, 66, include_tags=False,
                                   backtime=define.get_int(backtime), nexttime=define.get_int(nexttime)),
    ), title='Submission Notifications'))

import itertools

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define, message
from weasyl.controllers.decorators import login_required, token_checked

"""Contains view callables dealing with notification messages."""


@login_required
@token_checked
def messages_remove_(request):
    form = request.web_input(recall='', remove=[])
    remove_all_before = form.get('remove-all-before')

    if remove_all_before:
        message.remove_all_before(request.userid, int(remove_all_before))
    elif form.get('remove-all-submissions'):
        message.remove_all_submissions(request.userid, define.get_int(form['remove-all-submissions']))
    else:
        message.remove(request.userid, list(map(int, form.remove)))

    if form.recall:
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
        tag_section(message.select_site_updates(request.userid), 'notifications') +
        tag_section(message.select_comments(request.userid), 'comments') +
        tag_section(message.select_notifications(request.userid), 'notifications') +
        tag_section(message.select_journals(request.userid), 'journals')
    )

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/notifications.html", [
        sort_notifications(notifications),
    ]))


@login_required
def messages_submissions_(request):
    form = request.web_input(feature="", backtime=None, nexttime=None)

    define._page_header_info.refresh(request.userid)
    return Response(define.webpage(request.userid, "message/submissions_thumbnails.html", [
        # Feature
        form.feature,
        # Submissions
        message.select_submissions(request.userid, 66, include_tags=False,
                                   backtime=define.get_int(form.backtime), nexttime=define.get_int(form.nexttime)),
    ]))

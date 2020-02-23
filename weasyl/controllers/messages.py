from __future__ import absolute_import

import itertools
from collections import defaultdict

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from weasyl import define, message
from weasyl.controllers.decorators import login_required, token_checked

"""Contains view callables dealing with notification messages."""


@view_config(route_name="messages_remove", request_method="POST")
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
        message.remove(request.userid, map(int, form.remove))

    if form.recall:
        raise HTTPSeeOther(location="/messages/submissions")
    else:
        raise HTTPSeeOther(location="/messages/notifications")


def tag_section(results, section):
    for row in results:
        row['section'] = section
    return results


HEADERS = {
    1010: 'Journals',
    1015: 'Journals',
    3030: 'Collection Offers',
    3035: 'Collection Offers',
    3040: 'Collection Offers',
    3010: "Followers",
    3080: "Friend Requests",
    3085: "Friend Confirmations",
    3020: 'User Favorites',
    3100: 'User Favorites',
    3110: 'User Favorites',
    3050: "User Favorites",
    3070: 'Streaming',
    3075: "Streaming",
    3140: "Submission Tag Changes",
    3150: "Site Updates",
    4010: 'Shouts',
    4015: "Shouts",
    4016: "Staff Notes",
    4020: 'Submission Comments',
    4025: 'Submission Comments',
    4050: "Submission Comments",
    4030: 'Journal Comments',
    4035: 'Journal Comments',
    4060: 'Journal Comments',
    4065: "Journal Comments",
    4040: 'Character Comments',
    4045: "Character Comments"
}


def sort_notifications(notifications):
    # Not sure this sort is needed?
    notifications = [
        row
        for key, group in itertools.groupby(
            notifications, lambda row: message.notification_clusters.get(row['type']))
        for row in sorted(group, key=lambda row: row['unixtime'], reverse=True)
    ]

    notification_dict = defaultdict(list)
    for notification in notifications:
        if notification['type'] in HEADERS:
            header = HEADERS[notification['type']]
            notification_dict[header].append(notification)
        else:
            notification_dict['Miscellaneous'].append(notification)
    return notification_dict


@view_config(route_name="messages_notifications", renderer='/message/notifications.jinja2')
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
    return {'query': sort_notifications(notifications), 'title': 'Notifications'}


@view_config(route_name="messages_submissions", renderer='/message/submissions_thumbnails.jinja2')
@login_required
def messages_submissions_(request):
    form = request.web_input(feature="", backtime=None, nexttime=None)

    define._page_header_info.refresh(request.userid)
    return {
        'feature': form.feature,
        'query': message.select_submissions(request.userid, 66, include_tags=False,
                                            backtime=define.get_int(form.backtime),
                                            nexttime=define.get_int(form.nexttime))
    }

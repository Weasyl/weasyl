import itertools

import web

from weasyl import define, message
from weasyl.controllers.base import controller_base


# Message notification functions
class messages_remove_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(recall='', remove=[])
        remove_all_before = form.get('remove-all-before')

        if remove_all_before:
            message.remove_all_before(self.user_id, int(remove_all_before))
        elif form.get('remove-all-submissions'):
            message.remove_all_submissions(self.user_id, define.get_int(form['remove-all-submissions']))
        else:
            message.remove(self.user_id, map(int, form.remove))

        if form.recall:
            raise web.seeother('/messages/submissions')
        else:
            raise web.seeother('/messages/notifications')


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


class messages_notifications_(controller_base):
    login_required = True

    def GET(self):
        """ todo finish listing of message types in the template """

        notifications = (
            tag_section(message.select_site_updates(self.user_id), 'notifications') +
            tag_section(message.select_comments(self.user_id), 'comments') +
            tag_section(message.select_notifications(self.user_id), 'notifications') +
            tag_section(message.select_journals(self.user_id), 'journals')
        )

        define._page_header_info.refresh(self.user_id)
        return define.webpage(self.user_id, "message/notifications.html", [
            sort_notifications(notifications),
            self.user_id,
        ])


class messages_submissions_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(feature="", backtime=None, nexttime=None)

        define._page_header_info.refresh(self.user_id)
        return define.webpage(self.user_id, "message/submissions_thumbnails.html", [
            # Feature
            form.feature,
            # Submissions
            message.select_submissions(self.user_id, 66,
                                       backtime=define.get_int(form.backtime), nexttime=define.get_int(form.nexttime)),
            self.user_id,
        ])

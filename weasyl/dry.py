from __future__ import absolute_import

from libweasyl import staff

from weasyl import errorcode
from weasyl import define as d


def admin_render_page(template_path, args=()):
    userid = d.get_userid()
    status = d.common_status_check(userid)

    if status:
        return d.common_status_page(userid, status)
    elif not userid:
        return d.webpage(userid)
    elif userid not in staff.ADMINS:
        return d.webpage(userid, errorcode.permission)
    else:
        return d.webpage(userid, template_path, args)

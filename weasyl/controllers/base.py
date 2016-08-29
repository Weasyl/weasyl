import web

from libweasyl import staff

from weasyl import define, errorcode
import weasyl.api


class controller_base:
    login_required = False
    guest_required = False
    moderator_only = False
    admin_only = False
    disallow_api = False

    def status_check_fail(self, *args, **kwargs):
        return define.common_status_page(self.user_id, self.status)

    def permission_check_fail(self, *args, **kwargs):
        return define.errorpage(self.user_id, errorcode.permission)

    def login_check_fail(self, *args, **kwargs):
        return define.webpage(self.user_id)

    def login_guest_fail(self, *args, **kwargs):
        return define.webpage(self.user_id)

    def replace_methods(self, method):
        if hasattr(self, 'GET'):
            self.GET = method
        if hasattr(self, 'POST'):
            self.POST = method

    def GET(self, *args):
        raise web.notfound()

    def POST(self, *args):
        raise web.notfound()

    def __init__(self):
        if (self.disallow_api or self.moderator_only or self.admin_only) and weasyl.api.is_api_user():
            raise web.forbidden()

        self.user_id = define.get_userid()
        self.status = define.common_status_check(self.user_id)

        # Status check
        if self.status:
            self.replace_methods(self.status_check_fail)
            return

        # Guest check
        if self.guest_required and self.user_id != 0:
            self.replace_methods(self.login_guest_fail)
            return

        # Login check
        if self.login_required and self.user_id == 0:
            self.replace_methods(self.login_check_fail)
            return

        # Permission check
        if self.moderator_only and self.user_id not in staff.MODS:
            self.replace_methods(self.permission_check_fail)
            return
        if self.admin_only and self.user_id not in staff.ADMINS:
            self.replace_methods(self.permission_check_fail)
            return

import web

from weasyl import api, define, errorcode, login, moderation, \
    premiumpurchase, profile, resetpassword, template
from weasyl.controllers.base import controller_base


# Session management functions
class signin_(controller_base):
    guest_required = True

    def GET(self):
        return define.webpage(self.user_id, template.etc_signin, [
            False,
            web.ctx.environ.get('HTTP_REFERER', ''),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(username="", password="", referer="", sfwmode="nsfw")
        form.referer = form.referer or '/index'

        logid, logerror = login.authenticate_bcrypt(form.username, form.password)

        if logid and logerror == 'unicode-failure':
            raise web.seeother('/signin/unicode-failure')
        elif logid and logerror is None:
            if form.sfwmode == "sfw":
                web.setcookie("sfwmode", "sfw", 31536000)
            raise web.seeother(form.referer)
        elif logerror == "invalid":
            return define.webpage(self.user_id, template.etc_signin, [True, form.referer])
        elif logerror == "banned":
            reason = moderation.get_ban_reason(logid)
            return define.errorpage(
                self.user_id,
                "Your account has been permanently banned and you are no longer allowed "
                "to sign in.\n\n%s\n\nIf you believe this ban is in error, please "
                "contact support@weasyl.com for assistance." % (reason,))
        elif logerror == "suspended":
            suspension = moderation.get_suspension(logid)
            return define.errorpage(
                self.user_id,
                "Your account has been temporarily suspended and you are not allowed to "
                "be logged in at this time.\n\n%s\n\nThis suspension will be lifted on "
                "%s.\n\nIf you believe this suspension is in error, please contact "
                "support@weasyl.com for assistance." % (suspension.reason, define.convert_date(suspension.release)))
        elif logerror == "address":
            return "IP ADDRESS TEMPORARILY BLOCKED"

        return define.errorpage(self.user_id)


class signin_unicode_failure_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, 'etc/unicode_failure.html')

    def POST(self):
        form = web.input(password='', password_confirm='')
        login.update_unicode_password(self.user_id, form.password, form.password_confirm)
        raise web.webapi.Found('/')


class signout_(controller_base):
    login_required = True

    def GET(self):
        if api.is_api_user():
            raise web.webapi.Forbidden()
        if web.input(token="").token != define.get_token()[:8]:
            return define.errorpage(self.user_id, errorcode.token)

        login.signout(self.user_id)

        raise web.seeother("/index")


class signup_(controller_base):
    guest_required = True

    def GET(self):
        form = web.input(email="")

        return define.webpage(self.user_id, template.etc_signup, [
            # Signup data
            {
                "email": form.email,
                "username": None,
                "day": None,
                "month": None,
                "year": None,
                "error": None,
            },
        ])

    @define.token_checked
    def POST(self):
        form = web.input(
            username="", password="", passcheck="", email="", emailcheck="",
            day="", month="", year="", recaptcha_challenge_field="", recaptcha_response_field="")

        if not define.captcha_verify(form):
            return define.errorpage(
                self.user_id,
                "The image verification you entered was not correct; you should go back and try again.")

        login.create(form)
        return define.errorpage(
            self.user_id,
            "**Success!** Your username has been reserved and a "
            "message has been sent to the email address you specified with "
            "information on how to complete the registration process. You "
            "should receive this email within the next hour.",
            [["Return to the Home Page", "/index"]])


class verify_account_(controller_base):
    guest_required = True

    def GET(self):
        login.verify(web.input(token="").token)
        return define.errorpage(
            self.user_id,
            "**Success!** Your email address has been verified "
            "and you may now sign in to your account.",
            [["Sign In", "/signin"], ["Return to the Home Page", "/index"]])


class verify_premium_(controller_base):
    login_required = True

    def GET(self):
        premiumpurchase.verify(self.user_id, web.input(token="").token)
        return define.errorpage(
            self.user_id,
            "**Success!** Your purchased premium terms have "
            "been applied to your account.",
            [["Go to Premium " "Settings", "/control"], ["Return to the Home Page", "/index"]])


class forgotpassword_(controller_base):
    guest_required = True

    def GET(self):
        return define.webpage(self.user_id, template.etc_forgotpassword)

    @define.token_checked
    def POST(self):
        form = web.input(username="", email="", day="", month="", year="")

        resetpassword.request(form)
        return define.errorpage(
            self.user_id,
            "**Success!** A message containing information on "
            "how to reset your password has been sent to your email address.",
            [["Return to the Home Page", "/index"]])


class resetpassword_(controller_base):
    guest_required = True

    def GET(self):
        form = web.input(token="")

        if not resetpassword.checktoken(form.token):
            return define.errorpage(
                self.user_id,
                "This link does not appear to be valid. If you followed this link from your email, it may have expired.")

        resetpassword.prepare(form.token)

        return define.webpage(self.user_id, template.etc_resetpassword, [form.token])

    def POST(self):
        form = web.input(token="", username="", email="", day="", month="", year="", password="", passcheck="")

        resetpassword.reset(form)
        return define.errorpage(
            self.user_id,
            "**Success!** Your password has been reset and you may now sign in to your account.",
            [["Sign In", "/signin"], ["Return to the Home Page", "/index"]])


# Forced action functions
class force_resetpassword_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        if define.common_status_check(self.user_id) != "resetpassword":
            return define.errorpage(self.user_id, errorcode.permission)

        form = web.input(password="", passcheck="")

        resetpassword.force(self.user_id, form)
        raise web.seeother("/index")


class force_resetbirthday_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        if define.common_status_check(self.user_id) != "resetbirthday":
            return define.errorpage(self.user_id, errorcode.permission)

        form = web.input(birthday="")

        birthday = define.convert_inputdate(form.birthday)
        profile.force_resetbirthday(self.user_id, birthday)
        raise web.seeother("/index")

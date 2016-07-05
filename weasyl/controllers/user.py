from pyramid.httpexceptions import (
    HTTPFound,
    HTTPSeeOther,
)
from pyramid.response import Response
import web  # TODO: Remove me when this file is finished being ported to pyramid.

from weasyl import define, errorcode, login, moderation, \
    premiumpurchase, profile, resetpassword
from weasyl.controllers.decorators import (
    disallow_api,
    guest_required,
    login_required,
    token_checked,
)
from weasyl.controllers.decorators import controller_base  # TODO: Remove me when this file is finished being ported to pyramid.


# Session management functions

@guest_required
def signin_get_(request):
    return Response(define.webpage(request.userid, "etc/signin.html", [
        False,
        request.environ.get('HTTP_REFERER', ''),
    ]))


@token_checked
@guest_required
def signin_post_(request):
    form = request.web_input(username="", password="", referer="", sfwmode="nsfw")
    form.referer = form.referer or '/index'

    logid, logerror = login.authenticate_bcrypt(form.username, form.password)

    if logid and logerror == 'unicode-failure':
        return HTTPSeeOther(location='/signin/unicode-failure')
    elif logid and logerror is None:
        resp = HTTPSeeOther(location=form.referer)
        if form.sfwmode == "sfw":
            resp.set_cookie("sfwmode", "sfw", 31536000)
        return resp
    elif logerror == "invalid":
        return Response(define.webpage(request.userid, "etc/signin.html", [True, form.referer]))
    elif logerror == "banned":
        reason = moderation.get_ban_reason(logid)
        return Response(define.errorpage(
            request.userid,
            "Your account has been permanently banned and you are no longer allowed "
            "to sign in.\n\n%s\n\nIf you believe this ban is in error, please "
            "contact support@weasyl.com for assistance." % (reason,)))
    elif logerror == "suspended":
        suspension = moderation.get_suspension(logid)
        return Response(define.errorpage(
            request.userid,
            "Your account has been temporarily suspended and you are not allowed to "
            "be logged in at this time.\n\n%s\n\nThis suspension will be lifted on "
            "%s.\n\nIf you believe this suspension is in error, please contact "
            "support@weasyl.com for assistance." % (suspension.reason, define.convert_date(suspension.release))))
    elif logerror == "address":
        return Response("IP ADDRESS TEMPORARILY BLOCKED")

    return Response(define.errorpage(request.userid))


@login_required
def signin_unicode_failure_get_(request):
    return Response(define.webpage(request.userid, 'etc/unicode_failure.html'))


@login_required
def signin_unicode_failure_post_(request):
    form = request.web_input(password='', password_confirm='')
    login.update_unicode_password(request.userid, form.password, form.password_confirm)
    return HTTPFound(location="/", headers=request.response.headers)


@login_required
@disallow_api
def signout_(request):
    if request.web_input(token="").token != define.get_token()[:8]:
        return Response(define.errorpage(request.userid, errorcode.token))

    login.signout(request)

    raise HTTPSeeOther(location="/index", headers=request.response.headers)


@guest_required
def signup_get_(request):
    form = request.web_input(email="")

    return Response(define.webpage(request.userid, "etc/signup.html", [
        # Signup data
        {
            "email": form.email,
            "username": None,
            "day": None,
            "month": None,
            "year": None,
            "error": None,
        },
    ]))


@token_checked
@guest_required
def signup_post_(request):
    form = request.web_input(
        username="", password="", passcheck="", email="", emailcheck="",
        day="", month="", year="", recaptcha_challenge_field="",
        g_recaptcha_response=request.web_input("g-recaptcha-response"))

    if not define.captcha_verify(form):
        return Response(define.errorpage(
            request.userid,
            "There was an error validating the CAPTCHA response; you should go back and try again."))

    login.create(form)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your username has been reserved and a "
        "message has been sent to the email address you specified with "
        "information on how to complete the registration process. You "
        "should receive this email within the next hour.",
        [["Return to the Home Page", "/index"]]))


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
        return define.webpage(self.user_id, "etc/forgotpassword.html")

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

        return define.webpage(self.user_id, "etc/resetpassword.html", [form.token])

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

from __future__ import absolute_import

import urlparse

import arrow
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPSeeOther,
)
from pyramid.response import Response

from weasyl import define, errorcode, index, login, moderation, \
    premiumpurchase, profile, resetpassword, two_factor_auth
from weasyl.controllers.decorators import (
    disallow_api,
    guest_required,
    login_required,
    token_checked,
)


# Session management functions

@guest_required
def signin_get_(request):
    return Response(define.webpage(request.userid, "etc/signin.html", [
        False,
        request.environ.get('HTTP_REFERER', ''),
    ], title="Sign In"))


@guest_required
@token_checked
def signin_post_(request):
    form = request.web_input(username="", password="", referer="", sfwmode="nsfw")
    form.referer = form.referer or '/'

    logid, logerror = login.authenticate_bcrypt(form.username, form.password)

    if logid and logerror == 'unicode-failure':
        raise HTTPSeeOther(location='/signin/unicode-failure')
    elif logid and logerror is None:
        if form.sfwmode == "sfw":
            request.set_cookie_on_response("sfwmode", "sfw", 31536000)
        # Invalidate cached versions of the frontpage to respect the possibly changed SFW settings.
        index.template_fields.invalidate(logid)
        raise HTTPSeeOther(location=form.referer)
    elif logid and logerror == "2fa":
        # Password authentication passed, but user has 2FA set, so verify second factor (Also set SFW mode now)
        if form.sfwmode == "sfw":
            request.set_cookie_on_response("sfwmode", "sfw", 31536000)
        index.template_fields.invalidate(logid)
        # Check if out of recovery codes; this should *never* execute normally, save for crafted
        #   webtests. However, check for it and log an error to Sentry if it happens.
        remaining_recovery_codes = two_factor_auth.get_number_of_recovery_codes(logid)
        if remaining_recovery_codes == 0:
            raise RuntimeError("Two-factor Authentication: Count of recovery codes for userid " +
                               str(logid) + " was zero upon password authentication succeeding, " +
                               "which should be impossible.")
        # Store the authenticated userid & password auth time to the session
        sess = define.get_weasyl_session()
        # The timestamp at which password authentication succeeded
        sess.additional_data['2fa_pwd_auth_timestamp'] = arrow.now().timestamp
        # The userid of the user attempting authentication
        sess.additional_data['2fa_pwd_auth_userid'] = logid
        # The number of times the user has attempted to authenticate via 2FA
        sess.additional_data['2fa_pwd_auth_attempts'] = 0
        sess.save = True
        return Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(logid), form.referer, remaining_recovery_codes, None],
            title="Sign In - 2FA"
        ))
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


def _cleanup_2fa_session():
    """
    Cleans up a Weasyl session of any 2FA data stored during the authentication process.

    Parameters: None; keys off of the currently active session making the request.

    Returns: Nothing.
    """
    sess = define.get_weasyl_session()
    del sess.additional_data['2fa_pwd_auth_timestamp']
    del sess.additional_data['2fa_pwd_auth_userid']
    del sess.additional_data['2fa_pwd_auth_attempts']
    sess.save = True


@guest_required
def signin_2fa_auth_get_(request):
    sess = define.get_weasyl_session()

    # Only render page if the password has been authenticated (we have a UserID stored in the session)
    if '2fa_pwd_auth_userid' not in sess.additional_data:
        return Response(define.errorpage(request.userid, errorcode.permission))
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    # Maximum secondary authentication time: 5 minutes
    session_life = arrow.now().timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        _cleanup_2fa_session()
        return Response(define.errorpage(
            request.userid,
            errorcode.error_messages['TwoFactorAuthenticationAuthenticationTimeout'],
            [["Sign In", "/signin"], ["Return to the Home Page", "/"]]))
    else:
        ref = request.params["referer"] if "referer" in request.params else "/"
        return Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(tfa_userid), ref, two_factor_auth.get_number_of_recovery_codes(tfa_userid),
             None], title="Sign In - 2FA"))


@guest_required
@token_checked
def signin_2fa_auth_post_(request):
    sess = define.get_weasyl_session()

    # Only render page if the password has been authenticated (we have a UserID stored in the session)
    if '2fa_pwd_auth_userid' not in sess.additional_data:
        return Response(define.errorpage(request.userid, errorcode.permission))
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    session_life = arrow.now().timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        # Maximum secondary authentication time: 5 minutes
        _cleanup_2fa_session()
        return Response(define.errorpage(
            request.userid,
            errorcode.error_messages['TwoFactorAuthenticationAuthenticationTimeout'],
            [["Sign In", "/signin"], ["Return to the Home Page", "/"]]
        ))
    elif two_factor_auth.verify(tfa_userid, request.params["tfaresponse"]):
        # 2FA passed, so login and cleanup.
        _cleanup_2fa_session()
        login.signin(tfa_userid)
        ref = request.params["referer"] or "/"
        # User is out of recovery codes, so force-deactivate 2FA
        if two_factor_auth.get_number_of_recovery_codes(tfa_userid) == 0:
            two_factor_auth.force_deactivate(tfa_userid)
            return Response(define.errorpage(
                tfa_userid,
                errorcode.error_messages['TwoFactorAuthenticationZeroRecoveryCodesRemaining'],
                [["2FA Dashboard", "/control/2fa/status"], ["Return to the Home Page", "/"]]
            ))
        # Return to the target page, restricting to the path portion of 'ref' per urlparse.
        raise HTTPSeeOther(location=urlparse.urlparse(ref).path)
    elif sess.additional_data['2fa_pwd_auth_attempts'] >= 5:
        # Hinder brute-forcing the 2FA token or recovery code by enforcing an upper-bound on 2FA auth attempts.
        _cleanup_2fa_session()
        return Response(define.errorpage(
            request.userid,
            errorcode.error_messages['TwoFactorAuthenticationAuthenticationAttemptsExceeded'],
            [["Sign In", "/signin"], ["Return to the Home Page", "/"]]
        ))
    else:
        # Log the failed authentication attempt to the session and save
        sess.additional_data['2fa_pwd_auth_attempts'] += 1
        sess.save = True
        # 2FA failed; redirect to 2FA input page & inform user that authentication failed.
        return Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(tfa_userid), request.params["referer"], two_factor_auth.get_number_of_recovery_codes(tfa_userid),
             "2fa"], title="Sign In - 2FA"))


@login_required
def signin_unicode_failure_get_(request):
    return Response(define.webpage(request.userid, 'etc/unicode_failure.html'))


@login_required
def signin_unicode_failure_post_(request):
    form = request.web_input(password='', password_confirm='')
    login.update_unicode_password(request.userid, form.password, form.password_confirm)
    raise HTTPFound(location="/", headers=request.response.headers)


@login_required
@disallow_api
def signout_(request):
    if request.web_input(token="").token != define.get_token()[:8]:
        return Response(define.errorpage(request.userid, errorcode.token))

    login.signout(request)

    raise HTTPSeeOther(location="/", headers=request.response.headers)


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
    ], title="Create a Weasyl Account"))


@guest_required
@token_checked
def signup_post_(request):
    form = request.web_input(
        username="", password="", passcheck="", email="", emailcheck="",
        day="", month="", year="")

    if 'g-recaptcha-response' not in form or not define.captcha_verify(form['g-recaptcha-response']):
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
        [["Return to the Home Page", "/"]]))


@guest_required
def verify_account_(request):
    login.verify(request.web_input(token="").token)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your email address has been verified "
        "and you may now sign in to your account.",
        [["Sign In", "/signin"], ["Return to the Home Page", "/"]]))


@login_required
def verify_emailchange_get_(request):
    token = request.web_input(token="").token
    email = login.verify_email_change(request.userid, token)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your email address was successfully updated to **" + email + "**.",
        [["Return to the Home Page", "/"]]
    ))


@login_required
def verify_premium_(request):
    premiumpurchase.verify(request.userid, request.web_input(token="").token)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your purchased premium terms have "
        "been applied to your account.",
        [["Go to Premium " "Settings", "/control"], ["Return to the Home Page", "/"]]))


@guest_required
def forgotpassword_get_(request):
    return Response(define.webpage(request.userid, "etc/forgotpassword.html", title="Reset Forgotten Password"))


@guest_required
@token_checked
def forgetpassword_post_(request):
    form = request.web_input(username="", email="", day="", month="", year="")

    resetpassword.request(form)
    return Response(define.errorpage(
        request.userid,
        "**Success!** A message containing information on "
        "how to reset your password has been sent to your email address.",
        [["Return to the Home Page", "/"]]))


@guest_required
def resetpassword_get_(request):
    form = request.web_input(token="")

    if not resetpassword.checktoken(form.token):
        return Response(define.errorpage(
            request.userid,
            "This link does not appear to be valid. If you followed this link from your email, it may have expired."))

    resetpassword.prepare(form.token)

    return Response(define.webpage(request.userid, "etc/resetpassword.html", [form.token], title="Reset Forgotten Password"))


@guest_required
def resetpassword_post_(request):
    form = request.web_input(token="", username="", email="", day="", month="", year="", password="", passcheck="")

    resetpassword.reset(form)

    # Invalidate all other user sessions for this user.
    profile.invalidate_other_sessions(request.userid)

    return Response(define.errorpage(
        request.userid,
        "**Success!** Your password has been reset and you may now sign in to your account.",
        [["Sign In", "/signin"], ["Return to the Home Page", "/"]]))


# Forced action functions
@login_required
@token_checked
def force_resetpassword_(request):
    if define.common_status_check(request.userid) != "resetpassword":
        return Response(define.errorpage(request.userid, errorcode.permission))

    form = request.web_input(password="", passcheck="")

    resetpassword.force(request.userid, form)

    # Invalidate all other user sessions for this user.
    profile.invalidate_other_sessions(request.userid)

    raise HTTPSeeOther(location="/", headers=request.response.headers)


@login_required
@token_checked
def force_resetbirthday_(request):
    if define.common_status_check(request.userid) != "resetbirthday":
        return define.errorpage(request.userid, errorcode.permission)

    form = request.web_input(birthday="")

    birthday = define.convert_inputdate(form.birthday)
    profile.force_resetbirthday(request.userid, birthday)
    raise HTTPSeeOther(location="/", headers=request.response.headers)

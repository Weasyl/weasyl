from __future__ import absolute_import

import urlparse

import arrow
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPSeeOther,
)
from pyramid.view import view_config

from weasyl import define, index, login, moderation, \
    profile, resetpassword, two_factor_auth
from weasyl.controllers.decorators import (
    disallow_api,
    guest_required,
    login_required,
    token_checked,
)
from weasyl.error import WeasylError
from weasyl.macro import MACRO_SUPPORT_ADDRESS


# Session management functions
@view_config(route_name="signin", renderer='/etc/signin.jinja2', request_method='GET')
@guest_required
def signin_get_(request):
    return {
        'referer': request.environ.get('HTTP_REFERER', ''),
        'title': "Sign In"
    }


@view_config(route_name="signin", renderer='/etc/signin.jinja2', request_method='POST')
@guest_required
@token_checked
def signin_post_(request):
    form = request.web_input(username="", password="", referer="", sfwmode="nsfw")
    form.referer = form.referer or '/'

    logid, logerror = login.authenticate_bcrypt(form.username, form.password, request=request, ip_address=request.client_addr, user_agent=request.user_agent)

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
        # Ship the user off to the 2fa sign in page.
        return HTTPSeeOther(location=request.route_url('signin_2fa_auth'))

    elif logerror == "invalid":
        return {'error': True, 'referer': form.referer}
    elif logerror == "banned":
        reason = moderation.get_ban_reason(logid)
        return {
            'notification': "Your account has been permanently banned and you are no longer allowed "
                            "to sign in.\n\n%s\n\nIf you believe this ban is in error, please "
                            "contact %s for assistance." % (reason, MACRO_SUPPORT_ADDRESS),
            'title': "Sign In"
        }

    elif logerror == "suspended":
        suspension = moderation.get_suspension(logid)
        return {
            'notification': "Your account has been temporarily suspended and you are not allowed to "
                            "be logged in at this time.\n\n%s\n\nThis suspension will be lifted on "
                            "%s.\n\nIf you believe this suspension is in error, please contact "
                            "%s for assistance." % (suspension.reason, define.convert_date(suspension.release), MACRO_SUPPORT_ADDRESS),
            'title': "Sign In"
        }

    raise WeasylError("Unexpected")  # pragma: no cover


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


@view_config(route_name="signin_2fa_auth", renderer='/etc/signin_2fa_auth.jinja2', request_method='GET')
@guest_required
def signin_2fa_auth_get_(request):
    sess = define.get_weasyl_session()

    # Only render page if the session exists //and// the password has
    # been authenticated (we have a UserID stored in the session)
    if not sess.additional_data or '2fa_pwd_auth_userid' not in sess.additional_data:
        raise WeasylError('InsufficientPermissions')
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    # Maximum secondary authentication time: 5 minutes
    session_life = arrow.now().timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        _cleanup_2fa_session()
        raise WeasylError('TwoFactorAuthenticationAuthenticationTimeout')
    else:
        ref = request.params["referer"] if "referer" in request.params else "/"
        return {
            'username': define.get_display_name(tfa_userid),
            'referer': ref,
            'remaining_recovery_codes': two_factor_auth.get_number_of_recovery_codes(tfa_userid),
            'error': None,
            'title': "Sign In - 2FA"
        }


@view_config(route_name="signin_2fa_auth", renderer='/etc/signin_2fa_auth.jinja2', request_method='POST')
@guest_required
@token_checked
def signin_2fa_auth_post_(request):
    sess = define.get_weasyl_session()

    # Only render page if the session exists //and// the password has
    # been authenticated (we have a UserID stored in the session)
    if not sess.additional_data or '2fa_pwd_auth_userid' not in sess.additional_data:
        raise WeasylError('InsufficientPermissions')
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    session_life = arrow.now().timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        # Maximum secondary authentication time: 5 minutes
        _cleanup_2fa_session()
        raise WeasylError('TwoFactorAuthenticationAuthenticationTimeout')
    elif two_factor_auth.verify(tfa_userid, request.params["tfaresponse"]):
        # 2FA passed, so login and cleanup.
        _cleanup_2fa_session()
        login.signin(request, tfa_userid, ip_address=request.client_addr, user_agent=request.user_agent)
        ref = request.params["referer"] or "/"
        # User is out of recovery codes, so force-deactivate 2FA
        if two_factor_auth.get_number_of_recovery_codes(tfa_userid) == 0:
            two_factor_auth.force_deactivate(tfa_userid)
            raise WeasylError('TwoFactorAuthenticationZeroRecoveryCodesRemaining',
                              links=[["2FA Dashboard", "/control/2fa/status"], ["Return to the Home Page", "/"]])
        # Return to the target page, restricting to the path portion of 'ref' per urlparse.
        raise HTTPSeeOther(location=urlparse.urlparse(ref).path)
    elif sess.additional_data['2fa_pwd_auth_attempts'] >= 5:
        # Hinder brute-forcing the 2FA token or recovery code by enforcing an upper-bound on 2FA auth attempts.
        _cleanup_2fa_session()
        raise WeasylError('TwoFactorAuthenticationAuthenticationAttemptsExceeded',
                          links=[["Sign In", "/signin"], ["Return to the Home Page", "/"]])
    else:
        # Log the failed authentication attempt to the session and save
        sess.additional_data['2fa_pwd_auth_attempts'] += 1
        sess.save = True
        # 2FA failed; redirect to 2FA input page & inform user that authentication failed.
        return {
            'username': define.get_display_name(tfa_userid),
            'referer': request.params["referer"],
            'remaining_recovery_codes': two_factor_auth.get_number_of_recovery_codes(tfa_userid),
            'error': "2fa",
            'title': "Sign In - 2FA"
        }


@view_config(route_name='signin-unicode-failure', renderer='/etc/unicode_failure.jinja2', request_method="GET")
@login_required
def signin_unicode_failure_get_(request):
    return {'title': 'Fix Your Password'}


@view_config(route_name='signin-unicode-failure', renderer='/etc/unicode_failure.jinja2', request_method="POST")
@login_required
def signin_unicode_failure_post_(request):
    form = request.web_input(password='', password_confirm='')
    login.update_unicode_password(request.userid, form.password, form.password_confirm)
    raise HTTPFound(location="/", headers=request.response.headers)


@view_config(route_name='signout')
@login_required
@disallow_api
def signout_(request):
    if request.web_input(token="").token != define.get_token()[:8]:
        raise WeasylError('token')

    login.signout(request)

    raise HTTPSeeOther(location="/", headers=request.response.headers)


@view_config(route_name='signup', renderer='/etc/signup.jinja2', request_method="GET")
@guest_required
def signup_get_(request):
    return {'title': "Create a Weasyl Account"}


@view_config(route_name='signup', renderer='/etc/signup.jinja2', request_method="POST")
@guest_required
@token_checked
def signup_post_(request):
    form = request.web_input(
        username="", password="", passcheck="", email="", emailcheck="",
        day="", month="", year="")

    if not define.captcha_verify(form.get('g-recaptcha-response')):
        return {
            'error': "There was an error validating the CAPTCHA response;"
                     "you should go back and try again.",
            'title': "Create a Weasyl Account"
        }

    login.create(form)
    return {
        'success': "**Success!** Your username has been reserved and a message "
                   "has been sent to the email address you provided with "
                   "information on how to complete the registration process. You "
                   "should receive this email within the next hour.",
        'title': "Create a Weasyl Account"
    }


@view_config(route_name="verify_account", renderer='/etc/signup.jinja2')
@guest_required
def verify_account_(request):
    # TODO: Don't redirect back here after signing in for the first time. Errors due to being logged in
    login.verify(token=request.web_input(token="").token, ip_address=request.client_addr)
    return {
        'success': "**Success!** Your email address has been verified "
                   "and you may now sign in to your account.",
        'title': "Email Address Verified"
    }


@view_config(route_name="verify_emailchange", renderer='/etc/signup.jinja2')
@login_required
def verify_emailchange_get_(request):
    token = request.web_input(token="").token
    email = login.verify_email_change(request.userid, token)
    return {
        'success': "**Success!** Your email address was successfully updated to **{email}**.".format(email=email),
        'title': "Email Address Verified"
    }


@view_config(route_name="forgot_password", renderer='/etc/forgotpassword.jinja2', request_method="GET")
@guest_required
def forgotpassword_get_(request):
    return {'title': "Reset Forgotten Password"}


@view_config(route_name="forgot_password", renderer='/etc/forgotpassword.jinja2', request_method="POST")
@guest_required
@token_checked
def forgetpassword_post_(request):
    # TODO: Don't redirect back here after signing in for the first time. Errors due to being logged in
    form = request.web_input(email="")

    resetpassword.request(form)
    return {
        'error': "**Success!** Provided the supplied email matches a user account in our  "
                 "records, information on how to reset your password has been sent to your "
                 "email address.",
        'title': "Reset Forgotten Password"
    }


@view_config(route_name="reset_password", renderer='/etc/resetpassword.jinja2', request_method="GET")
@guest_required
def resetpassword_get_(request):
    form = request.web_input(token="")

    if not resetpassword.prepare(form.token):
        return {
            'error': "This link does not appear to be valid. "
                     "If you followed this link from your email, it may have expired.",
            'title': "Reset Forgotten Password"
            }

    return {'token': form.token, 'title': "Reset Forgotten Password"}


@view_config(route_name="reset_password", renderer='/etc/resetpassword.jinja2', request_method="POST")
@guest_required
def resetpassword_post_(request):
    form = request.web_input(token="", username="", email="", day="", month="", year="", password="", passcheck="")

    resetpassword.reset(form)

    # Invalidate all other user sessions for this user.
    profile.invalidate_other_sessions(request.userid)
    return {
        'error':  "**Success!** Your password has been reset and you may now sign in to your account.",
        'title': "Reset Forgotten Password"
    }


# Forced action functions
@view_config(route_name="force_reset_password", request_method="POST")
@login_required
@token_checked
def force_resetpassword_(request):
    if define.common_status_check(request.userid) != "resetpassword":
        raise WeasylError('InsufficientPermissions')

    form = request.web_input(password="", passcheck="")

    resetpassword.force(request.userid, form)

    # Invalidate all other user sessions for this user.
    profile.invalidate_other_sessions(request.userid)

    raise HTTPSeeOther(location="/", headers=request.response.headers)


@view_config(route_name="force_reset_birthday", request_method="POST")
@login_required
@token_checked
def force_resetbirthday_(request):
    if define.common_status_check(request.userid) != "resetbirthday":
        raise WeasylError('permission')

    form = request.web_input(birthday="")

    birthday = define.convert_inputdate(form.birthday)
    profile.force_resetbirthday(request.userid, birthday)
    raise HTTPSeeOther(location="/", headers=request.response.headers)


@view_config(route_name="vouch", request_method="POST")
@login_required
@token_checked
def vouch_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    targetid = int(request.POST['targetid'])

    result = define.engine.execute(
        "UPDATE login SET voucher = %(voucher)s WHERE userid = %(target)s AND voucher IS NULL",
        voucher=request.userid,
        target=targetid,
    )

    if result.rowcount != 0:
        define._get_all_config.invalidate(targetid)

    target_username = define.get_display_name(targetid)

    if target_username is None:
        assert result.rowcount == 0
        raise WeasylError("Unexpected")

    raise HTTPSeeOther(location=request.route_path('profile_tilde', name=define.get_sysname(target_username)))

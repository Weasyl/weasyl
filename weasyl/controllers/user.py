import arrow
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response
from sqlalchemy.orm.attributes import flag_modified

from weasyl import (
    define,
    emailer,
    login,
    moderation,
    profile,
    resetpassword,
    turnstile,
    two_factor_auth,
)
from weasyl.controllers.decorators import (
    disallow_api,
    guest_required,
    login_required,
    token_checked,
)
from weasyl.error import WeasylError
from weasyl.sessions import create_session


# Session management functions

@guest_required
def signin_get_(request):
    return Response(define.webpage(request.userid, "etc/signin.html", (False, ""), title="Sign In"))


@guest_required
@token_checked
def signin_post_(request):
    form = request.web_input(username="", password="", sfwmode="nsfw")
    referer = request.POST.get("referer") or "/"

    logid, logerror = login.authenticate_bcrypt(form.username, form.password, request=request, ip_address=request.client_addr, user_agent=request.user_agent)

    if logid and logerror is None:
        response = HTTPSeeOther(location=define.path_redirect(referer))
        response.set_cookie('WZL', request.weasyl_session.sessionid, max_age=60 * 60 * 24 * 365,
                            secure=request.scheme == 'https', httponly=True)
        if form.sfwmode == "sfw":
            response.set_cookie("sfwmode", "sfw", max_age=31536000)
        return response
    elif logid and logerror == "2fa":
        # Password authentication passed, but user has 2FA set, so verify second factor
        # Check if out of recovery codes; this should *never* execute normally, save for crafted
        #   webtests. However, check for it and log an error to Sentry if it happens.
        remaining_recovery_codes = two_factor_auth.get_number_of_recovery_codes(logid)
        if remaining_recovery_codes == 0:
            raise RuntimeError("Two-factor Authentication: Count of recovery codes for userid " +
                               str(logid) + " was zero upon password authentication succeeding, " +
                               "which should be impossible.")

        with define.sessionmaker_future.begin() as tx:
            sess = request.weasyl_session = create_session(None)
            sess.additional_data = {
                # The timestamp at which password authentication succeeded
                '2fa_pwd_auth_timestamp': arrow.utcnow().int_timestamp,
                # The userid of the user attempting authentication
                '2fa_pwd_auth_userid': logid,
                # The number of times the user has attempted to authenticate via 2FA
                '2fa_pwd_auth_attempts': 0,
            }
            tx.add(sess)

        response = Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(logid), referer, remaining_recovery_codes, None],
            title="Sign In - 2FA"
        ))
        response.set_cookie('WZL', sess.sessionid, max_age=60 * 60 * 24 * 365,
                            secure=request.scheme == 'https', httponly=True)
        if form.sfwmode == "sfw":
            response.set_cookie("sfwmode", "sfw", max_age=31536000)
        return response
    elif logerror == "invalid":
        return Response(define.webpage(request.userid, "etc/signin.html", [True, referer]))
    elif logerror == "banned":
        message = moderation.get_ban_message(logid)
        return Response(define.errorpage(request.userid, message))
    elif logerror == "suspended":
        message = moderation.get_suspension_message(logid)
        return Response(define.errorpage(request.userid, message))

    raise WeasylError("Unexpected")  # pragma: no cover


@guest_required
def signin_2fa_auth_get_(request):
    sess = request.weasyl_session

    # Only render page if the session exists //and// the password has
    # been authenticated (we have a UserID stored in the session)
    if sess is None or not sess.additional_data or '2fa_pwd_auth_userid' not in sess.additional_data:
        raise WeasylError('InsufficientPermissions')
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    # Maximum secondary authentication time: 5 minutes
    session_life = arrow.utcnow().int_timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        login.signout(request)
        raise WeasylError('TwoFactorAuthenticationAuthenticationTimeout')
    else:
        ref = "/"
        return Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(tfa_userid), ref, two_factor_auth.get_number_of_recovery_codes(tfa_userid),
             None], title="Sign In - 2FA"))


@guest_required
@token_checked
def signin_2fa_auth_post_(request):
    sess = request.weasyl_session

    # Only render page if the session exists //and// the password has
    # been authenticated (we have a UserID stored in the session)
    if sess is None or not sess.additional_data or '2fa_pwd_auth_userid' not in sess.additional_data:
        raise WeasylError('InsufficientPermissions')
    tfa_userid = sess.additional_data['2fa_pwd_auth_userid']

    session_life = arrow.utcnow().int_timestamp - sess.additional_data['2fa_pwd_auth_timestamp']
    if session_life > 300:
        # Maximum secondary authentication time: 5 minutes
        login.signout(request)
        raise WeasylError('TwoFactorAuthenticationAuthenticationTimeout')
    elif two_factor_auth.verify(tfa_userid, request.params["tfaresponse"]):
        # 2FA passed, so login and cleanup.
        login.signout(request)
        login.signin(request, tfa_userid, ip_address=request.client_addr, user_agent=request.user_agent)
        # User is out of recovery codes, so force-deactivate 2FA
        if two_factor_auth.get_number_of_recovery_codes(tfa_userid) == 0:
            two_factor_auth.force_deactivate(tfa_userid)
            raise WeasylError('TwoFactorAuthenticationZeroRecoveryCodesRemaining',
                              links=[["2FA Dashboard", "/control/2fa/status"], ["Return to the Home Page", "/"]])
        # Return to the target page.
        ref = request.POST["referer"] or "/"
        response = HTTPSeeOther(location=define.path_redirect(ref))
        response.set_cookie('WZL', request.weasyl_session.sessionid, max_age=60 * 60 * 24 * 365,
                            secure=request.scheme == 'https', httponly=True)
        return response
    elif sess.additional_data['2fa_pwd_auth_attempts'] >= 5:
        # Hinder brute-forcing the 2FA token or recovery code by enforcing an upper-bound on 2FA auth attempts.
        login.signout(request)
        raise WeasylError('TwoFactorAuthenticationAuthenticationAttemptsExceeded',
                          links=[["Sign In", "/signin"], ["Return to the Home Page", "/"]])
    else:
        # Log the failed authentication attempt to the session and save
        with define.sessionmaker_future.begin() as tx:
            sess.additional_data['2fa_pwd_auth_attempts'] += 1
            flag_modified(sess, 'additional_data')
            tx.add(sess)
        # 2FA failed; respond with 2FA input page & inform user that authentication failed.
        return Response(define.webpage(
            request.userid,
            "etc/signin_2fa_auth.html",
            [define.get_display_name(tfa_userid), request.POST["referer"], two_factor_auth.get_number_of_recovery_codes(tfa_userid),
             "2fa"], title="Sign In - 2FA"))


@token_checked
@disallow_api
def signout_(request):
    if request.userid != 0:
        login.signout(request)

    response = HTTPSeeOther(location="/")
    response.delete_cookie('WZL')
    response.delete_cookie('sfwmode')
    return response


@guest_required
def signup_get_(request):
    return Response(define.webpage(request.userid, "etc/signup.html", (), options=("signup",), title="Create a Weasyl Account"))


@guest_required
@token_checked
def signup_post_(request):
    turnstile.require(request)

    form = request.web_input(
        username="", password="", email="")

    login.create(form)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your username has been reserved and a message "
        "has been sent to the email address you provided with "
        "information on how to complete the registration process. You "
        "should receive this email within the next hour.",
        [["Return to the Home Page", "/"]]))


@guest_required
def verify_account_(request):
    login.verify(token=request.web_input(token="").token, ip_address=request.client_addr)
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


@guest_required
def forgotpassword_get_(request):
    return Response(define.webpage(request.userid, "etc/forgotpassword.html", title="Reset Forgotten Password"))


@guest_required
@token_checked
def forgetpassword_post_(request):
    turnstile.require(request)

    resetpassword.request(email=request.POST['email'])
    return Response(define.errorpage(
        request.userid,
        "**Success!** Information on how to reset your password has been sent to your email address.",
        [["Return to the Home Page", "/"]]))


@guest_required
def resetpassword_get_(request):
    token = request.GET.get('token', "")
    reset_target = resetpassword.prepare(token=token)

    if reset_target is None:
        return Response(define.errorpage(
            request.userid,
            "This link does not appear to be valid. If you followed this link from your email, it may have expired."))

    if isinstance(reset_target, resetpassword.Unregistered):
        return Response(define.errorpage(
            request.userid,
            "The e-mail address **%s** is not associated with a Weasyl account." % (reset_target.email,),
            [["Sign Up", "/signup"], ["Return to the Home Page", "/"]]))

    return Response(define.webpage(request.userid, "etc/resetpassword.html", [token, reset_target], options=("signup",), title="Reset Forgotten Password"))


@guest_required
def resetpassword_post_(request):
    expect_userid = int(request.POST['userid'])

    resetpassword.reset(
        token=request.POST['token'],
        password=request.POST['password'],
        expect_userid=expect_userid,
        address=request.client_addr,
    )

    # Invalidate user sessions for this user.
    profile.invalidate_other_sessions(expect_userid)

    return Response(define.errorpage(
        request.userid,
        "**Success!** Your password has been reset and you may now sign in to your account.",
        [["Sign In", "/signin"], ["Return to the Home Page", "/"]]))


@login_required
@token_checked
def vouch_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    targetid = int(request.POST['targetid'])

    updated = define.engine.execute(
        "UPDATE login SET voucher = %(voucher)s WHERE userid = %(target)s AND voucher IS NULL RETURNING email",
        voucher=request.userid,
        target=targetid,
    ).first()

    target_username = define.try_get_display_name(targetid)

    if updated is not None:
        define._get_all_config.invalidate(targetid)
        emailer.send(updated.email, "Weasyl Account Verified", define.render("email/verified.html", [target_username]))

    if target_username is None:
        assert updated is None
        raise WeasylError("Unexpected")

    raise HTTPSeeOther(location=request.route_path('profile_tilde', name=define.get_sysname(target_username)))

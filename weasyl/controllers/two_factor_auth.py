import arrow
from pyramid.response import Response
from pyramid.httpexceptions import HTTPSeeOther
from sqlalchemy.orm.attributes import flag_modified

from weasyl import define
from weasyl import login
from weasyl import two_factor_auth as tfa
from weasyl.controllers.decorators import (
    login_required,
    token_checked,
    twofactorauth_disabled_required,
    twofactorauth_enabled_required,
)
from weasyl.error import WeasylError
from weasyl.profile import invalidate_other_sessions


def _set_totp_code_on_session(request, totp_code):
    sess = request.weasyl_session

    with define.sessionmaker_future.begin() as tx:
        sess.additional_data['2fa_totp_code'] = totp_code
        flag_modified(sess, 'additional_data')
        tx.add(sess)


def _get_totp_code_from_session(request):
    return request.weasyl_session.additional_data['2fa_totp_code']


def _set_recovery_codes_on_session(request, recovery_codes):
    sess = request.weasyl_session

    with define.sessionmaker_future.begin() as tx:
        sess.additional_data['2fa_recovery_codes'] = recovery_codes
        sess.additional_data['2fa_recovery_codes_timestamp'] = arrow.utcnow().int_timestamp
        flag_modified(sess, 'additional_data')
        tx.add(sess)


def _get_recovery_codes_from_session(request):
    return request.weasyl_session.additional_data.get('2fa_recovery_codes')


def _cleanup_session(request):
    sess = request.weasyl_session

    with define.sessionmaker_future.begin() as tx:
        sess.additional_data.pop('2fa_recovery_codes', None)
        sess.additional_data.pop('2fa_recovery_codes_timestamp', None)
        sess.additional_data.pop('2fa_totp_code', None)
        flag_modified(sess, 'additional_data')
        tx.add(sess)


@login_required
def tfa_status_get_(request):
    return Response(define.webpage(request.userid, "control/2fa/status.html", [
        tfa.is_2fa_enabled(request.userid), tfa.get_number_of_recovery_codes(request.userid)
    ], title="2FA Status"))


@login_required
@twofactorauth_disabled_required
def tfa_init_get_(request):
    return Response(define.webpage(request.userid, "control/2fa/init.html", [
        define.get_username(request.userid),
        None
    ], title="Enable 2FA: Step 1"))


@login_required
@token_checked
@twofactorauth_disabled_required
def tfa_init_post_(request):
    username = define.get_username(request.userid)
    auth_result = login.authenticate_bcrypt(
        username=username.sysname,
        password=request.POST.getone('password'),
        request=None,
    )

    if auth_result == login.Success(request.userid):
        # The user has authenticated, so continue with the initialization process.
        tfa_secret, tfa_qrcode = tfa.init(request.userid)
        _set_totp_code_on_session(request, tfa_secret)
        return Response(define.webpage(request.userid, "control/2fa/init_qrcode.html", [
            username,
            tfa_secret,
            tfa_qrcode,
            None
        ], title="Enable 2FA: Step 2"))
    else:
        # XXX: Other states are possible, but treating them as an authentication failure is acceptable for now.
        assert isinstance(auth_result, login.InvalidCredentials)

        # The user's password failed to authenticate
        return Response(define.webpage(request.userid, "control/2fa/init.html", [
            define.get_display_name(request.userid),
            "password"
        ], title="Enable 2FA: Step 1"))


@login_required
@twofactorauth_disabled_required
def tfa_init_qrcode_get_(request):
    """
    IMPLEMENTATION NOTE: This page cannot be accessed directly (HTTP GET), as the user has not yet
    verified ownership over the account by verifying their password. That said, be helpful and inform
    the user of this instead of erroring without explanation.
    """
    raise HTTPSeeOther(location="/control/2fa/status")


@login_required
@token_checked
@twofactorauth_disabled_required
def tfa_init_qrcode_post_(request):
    # Strip any spaces from the TOTP code (some authenticators display the digits like '123 456')
    tfaresponse = request.params['tfaresponse'].replace(' ', '')
    tfa_secret_sess = _get_totp_code_from_session(request)

    # Check to see if the tfaresponse matches the tfasecret when run through the TOTP algorithm
    tfa_secret, recovery_codes = tfa.init_verify_tfa(tfa_secret_sess, tfaresponse)

    # The 2FA TOTP code did not match with the generated 2FA secret
    if not tfa_secret:
        return Response(define.webpage(request.userid, "control/2fa/init_qrcode.html", [
            define.get_username(request.userid),
            tfa_secret_sess,
            tfa.generate_tfa_qrcode(request.userid, tfa_secret_sess),
            "2fa"
        ], title="Enable 2FA: Step 2"))
    else:
        _set_recovery_codes_on_session(request, ','.join(recovery_codes))
        return Response(define.webpage(request.userid, "control/2fa/init_verify.html", [
            recovery_codes,
            None
        ], title="Enable 2FA: Final Step"))


@login_required
@twofactorauth_disabled_required
def tfa_init_verify_get_(request):
    """
    IMPLEMENTATION NOTE: This page cannot be accessed directly (HTTP GET), as the user needs to both verify
    their password to assert ownership of their account (`tfa_init_*_()`), and needs to be provided with their
    TOTP provisioning QRcode/secret key, and prove that they have successfully loaded it to their 2FA authenticator
    of choice (`tfa_init_qrcode_*_()`). That said, be helpful and inform the user of this instead of erroring without
    explanation.
    """
    raise HTTPSeeOther(location="/control/2fa/status")


@login_required
@token_checked
@twofactorauth_disabled_required
def tfa_init_verify_post_(request):
    # Extract parameters from the form
    verify_checkbox = 'verify' in request.params
    tfasecret = _get_totp_code_from_session(request)
    tfarecoverycodes = _get_recovery_codes_from_session(request)

    # Does the user want to proceed with enabling 2FA?
    if verify_checkbox and tfa.store_recovery_codes(request.userid, tfarecoverycodes):
        # Strip any spaces from the TOTP code (some authenticators display the digits like '123 456')
        tfaresponse = request.params['tfaresponse'].replace(' ', '')

        # TOTP+2FA Secret validates (activate & redirect to status page)
        if tfa.activate(request.userid, tfasecret, tfaresponse):
            # Invalidate all other login sessions
            invalidate_other_sessions(request.userid)
            # Clean up the stored session variables
            _cleanup_session(request)
            raise HTTPSeeOther(location="/control/2fa/status")
        # TOTP+2FA Secret did not validate
        else:
            return Response(define.webpage(request.userid, "control/2fa/init_verify.html", [
                tfarecoverycodes.split(','),
                "2fa"
            ], title="Enable 2FA: Final Step"))
    # The user didn't check the verification checkbox (despite HTML5's client-side check); regenerate codes & redisplay
    elif not verify_checkbox:
        return Response(define.webpage(request.userid, "control/2fa/init_verify.html", [
            tfarecoverycodes.split(','),
            "verify"
        ], title="Enable 2FA: Final Step"))


@login_required
@twofactorauth_enabled_required
def tfa_disable_get_(request):
    return Response(define.webpage(request.userid, "control/2fa/disable.html", [
        define.get_username(request.userid),
        None
    ], title="Disable 2FA"))


@login_required
@token_checked
@twofactorauth_enabled_required
def tfa_disable_post_(request):
    tfaresponse = request.params['tfaresponse']
    verify_checkbox = 'verify' in request.params

    if verify_checkbox:
        # If 2FA was successfully deactivated... return to 2FA dashboard
        if tfa.deactivate(request.userid, tfaresponse):
            raise HTTPSeeOther(location="/control/2fa/status")
        else:
            return Response(define.webpage(request.userid, "control/2fa/disable.html", [
                define.get_username(request.userid),
                "2fa"
            ], title="Disable 2FA"))
    else:
        # The user didn't check the verification checkbox (despite HTML5's client-side check)
        return Response(define.webpage(request.userid, "control/2fa/disable.html", [
            define.get_username(request.userid),
            "verify"
        ], title="Disable 2FA"))


@login_required
@twofactorauth_enabled_required
def tfa_generate_recovery_codes_verify_password_get_(request):
    return Response(define.webpage(
        request.userid,
        "control/2fa/generate_recovery_codes_verify_password.html",
        [None],
        title="Generate Recovery Codes: Verify Password"
    ))


@token_checked
@login_required
@twofactorauth_enabled_required
def tfa_generate_recovery_codes_verify_password_post_(request):
    username = define.get_username(request.userid)
    auth_result = login.authenticate_bcrypt(
        username=username.sysname,
        password=request.POST.getone('password'),
        request=None,
    )
    if auth_result == login.SecondFactorRequired(request.userid):
        # The user has authenticated, so continue with generating the new recovery codes.

        # Edge case prevention: Stop the user from having two Weasyl sessions open and trying
        #   to proceed through the generation process with two sets of recovery codes.
        invalidate_other_sessions(request.userid)
        # Edge case prevention: Do we have existing (and recent) codes on this session? Prevent
        #   a user from confusing themselves if they visit the request page twice.
        sess = request.weasyl_session
        gen_rec_codes = True
        if '2fa_recovery_codes_timestamp' in sess.additional_data:
            # Are the codes on the current session < 30 minutes old?
            tstamp = sess.additional_data['2fa_recovery_codes_timestamp']
            if arrow.utcnow().int_timestamp - tstamp < 1800:
                # We have recent codes on the session, use them instead of generating fresh codes.
                recovery_codes = sess.additional_data['2fa_recovery_codes'].split(',')
                gen_rec_codes = False
        if gen_rec_codes:
            # Either this is a fresh request to generate codes, or the timelimit was exceeded.
            recovery_codes = tfa.generate_recovery_codes()
            _set_recovery_codes_on_session(request, ','.join(recovery_codes))
        return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
            recovery_codes,
            None
        ], title="Generate Recovery Codes: Save New Recovery Codes"))
    else:
        # XXX: Other states are possible, but treating them as an authentication failure is acceptable for now.
        assert isinstance(auth_result, login.InvalidCredentials)

        # The user's password failed to authenticate
        return Response(define.webpage(
            request.userid,
            "control/2fa/generate_recovery_codes_verify_password.html",
            ["password"],
            title="Generate Recovery Codes: Verify Password"
        ))


@login_required
@twofactorauth_enabled_required
def tfa_generate_recovery_codes_get_(request):
    """
    IMPLEMENTATION NOTE: This page cannot be accessed directly (HTTP GET), as the user may not have verified
    control over the account by providing their password. Further, prevent edge cases where a user may
    (un)intentionally attempt to encounter edge cases, such as having two browsers or windows open and generate
    a situation where it isn't obvious which set of recovery codes will be saved; all other sessions are cleared
    in this path to prevent this. That said, be nice and tell the user where to go to proceed.
    """
    # Inform the user of where to go to begin
    raise HTTPSeeOther(location="/control/2fa/status")


@login_required
@token_checked
@twofactorauth_enabled_required
def tfa_generate_recovery_codes_post_(request):
    # Extract parameters from the form
    verify_checkbox = 'verify' in request.params
    tfaresponse = request.params['tfaresponse']
    tfarecoverycodes = _get_recovery_codes_from_session(request)

    # Does the user want to save the new recovery codes?
    if verify_checkbox:
        if tfa.verify(request.userid, tfaresponse, consume_recovery_code=False):
            if tfa.store_recovery_codes(request.userid, tfarecoverycodes):
                # Clean up the stored session variables
                _cleanup_session(request)
                # Successfuly stored new recovery codes.
                raise HTTPSeeOther(location="/control/2fa/status")
            else:
                # Recovery code string was corrupted or otherwise altered.
                raise WeasylError("Unexpected")
        else:
            return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
                tfarecoverycodes.split(','),
                "2fa"
            ], title="Generate Recovery Codes: Save New Recovery Codes"))
    elif not verify_checkbox:
        return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
            tfarecoverycodes.split(','),
            "verify"
        ], title="Generate Recovery Codes: Save New Recovery Codes"))

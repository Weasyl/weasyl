from __future__ import absolute_import, unicode_literals

from pyramid.response import Response
from pyramid.httpexceptions import HTTPSeeOther

from weasyl import define
from weasyl import login
from weasyl import two_factor_auth as tfa
from weasyl.controllers.decorators import (
    login_required,
    token_checked,
)
from weasyl.error import WeasylError
from weasyl.profile import invalidate_other_sessions


def _error_if_2fa_enabled(userid):
    """
    In lieu of a module-specific decorator, this function returns an error if 2FA is enabled, preventing the user
    from self-wiping their own 2FA Secret (AKA, re-setting up 2FA while it is already enabled)
    """
    if tfa.is_2fa_enabled(userid):
        return Response(define.errorpage(userid, "2FA is already configured for this account.", [
            ["Go Back", "/control"], ["Return to the Home Page", "/"]
        ]))


def _error_if_2fa_is_not_enabled(userid):
    """
    In lieu of a module-specific decorator, this function returns an error if 2FA is not enabled.
    """
    if not tfa.is_2fa_enabled(userid):
        return Response(define.errorpage(userid, "2FA is not configured for this account.", [
            ["Go Back", "/control"], ["Return to the Home Page", "/"]
        ]))


@login_required
def tfa_status_get_(request):
    return Response(define.webpage(request.userid, "control/2fa/status.html", [
        tfa.is_2fa_enabled(request.userid), tfa.get_number_of_recovery_codes(request.userid)
    ]))


@login_required
def tfa_init_get_(request):
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # Otherwise, render the page
    return Response(define.webpage(request.userid, "control/2fa/init.html", [
        define.get_display_name(request.userid),
        None
    ]))


@login_required
@token_checked
def tfa_init_post_(request):
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # Otherwise, process the form
    if request.params['action'] == "continue":
        userid, status = login.authenticate_bcrypt(define.get_display_name(request.userid),
                                                   request.params['password'], session=False)
        # The user's password failed to authenticate
        if status == "invalid":
            return Response(define.webpage(request.userid, "control/2fa/init.html", [
                define.get_display_name(request.userid),
                "password"
            ]))
        # Unlikely that this block will get triggered, but just to be safe, check for it
        elif status == "unicode-failure":
            raise HTTPSeeOther(location='/signin/unicode-failure')
        # The user has authenticated, so continue with the initialization process.
        else:
            tfa_secret, tfa_qrcode = tfa.init(request.userid)
            return Response(define.webpage(request.userid, "control/2fa/init_qrcode.html", [
                define.get_display_name(request.userid),
                tfa_secret,
                tfa_qrcode,
                None
            ]))
    else:
        # This shouldn't be reached normally (user intentionally altered action?)
        raise WeasylError("Unexpected")


@login_required
def tfa_init_qrcode_get_(request):
    """
    IMPLEMENTATION NOTE: This page cannot be accessed directly (HTTP GET), as the user has not yet
    verified ownership over the account by verifying their password. That said, be helpful and inform
    the user of this instead of erroring without explanation.
    """
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # If 2FA is not enabled, inform the user of where to go to begin
    return Response(define.errorpage(
                    request.userid,
                    """This page cannot be accessed directly, and must be accessed as part of the 2FA
                    setup process. Click <b>2FA Status</b>, below, to go to the 2FA Dashboard to begin.""",
                    [["2FA Status", "/control/2fa/status"], ["Return to the Home Page", "/"]]))


@login_required
@token_checked
def tfa_init_qrcode_post_(request):
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # Otherwise, process the form
    if request.params['action'] == "continue":
        # Strip any spaces from the TOTP code (some authenticators display the digits like '123 456')
        tfaresponse = request.params['tfaresponse'].replace(' ', '')

        # Check to see if the tfaresponse matches the tfasecret when run through the TOTP algorithm
        tfa_secret, recovery_codes = tfa.init_verify_tfa(request.userid, request.params['tfasecret'], tfaresponse)

        # The 2FA TOTP code did not match with the generated 2FA secret
        if not tfa_secret:
            return Response(define.webpage(request.userid, "control/2fa/init_qrcode.html", [
                define.get_display_name(request.userid),
                request.params['tfasecret'],
                tfa.generate_tfa_qrcode(request.userid, request.params['tfasecret']),
                "2fa"
            ]))
        else:
            return Response(define.webpage(request.userid, "control/2fa/init_verify.html",
                            [tfa_secret, recovery_codes, None]))
    else:
        # This shouldn't be reached normally (user intentionally altered action?)
        raise WeasylError("Unexpected")


@login_required
def tfa_init_verify_get_(request):
    """
    IMPLEMENTATION NOTE: This page cannot be accessed directly (HTTP GET), as the user needs to both verify
    their password to assert ownership of their account (`tfa_init_*_()`), and needs to be provided with their
    TOTP provisioning QRcode/secret key, and prove that they have successfully loaded it to their 2FA authenticator
    of choice (`tfa_init_qrcode_*_()`). That said, be helpful and inform the user of this instead of erroring without
    explanation.
    """
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # If 2FA is not enabled, inform the user of where to go to begin
    return Response(define.errorpage(
                    request.userid,
                    """This page cannot be accessed directly, and must be accessed as part of the 2FA
                    setup process. Click <b>2FA Status</b>, below, to go to the 2FA Dashboard to begin.""",
                    [["2FA Status", "/control/2fa/status"], ["Return to the Home Page", "/"]]))


@login_required
@token_checked
def tfa_init_verify_post_(request):
    # Return an error if 2FA is already enabled (there's nothing to do in this route)
    _error_if_2fa_enabled(request.userid)

    # Extract parameters from the form
    action = request.params['action']
    verify_checkbox = request.params['verify']
    tfasecret = request.params['tfasecret']
    tfaresponse = request.params['tfaresponse']
    tfarecoverycodes = request.params['tfarecoverycodes']

    # Does the user want to proceed with enabling 2FA?
    if action == "enable" and verify_checkbox and tfa.store_recovery_codes(request.userid, tfarecoverycodes):
        # Strip any spaces from the TOTP code (some authenticators display the digits like '123 456')
        tfaresponse = request.params['tfaresponse'].replace(' ', '')

        # TOTP+2FA Secret validates (activate & redirect to status page)
        if tfa.activate(request.userid, tfasecret, tfaresponse):
            # Invalidate all other login sessions
            invalidate_other_sessions(request.userid)
            raise HTTPSeeOther(location="/control/2fa/status")
        # TOTP+2FA Secret did not validate
        else:
            return Response(define.webpage(request.userid, "control/2fa/init_verify.html",
                            [tfasecret, tfarecoverycodes.split(','), "2fa"]))
    # The user didn't check the verification checkbox (despite HTML5's client-side check); regenerate codes & redisplay
    elif action == "enable" and not verify_checkbox:
        return Response(define.webpage(request.userid, "control/2fa/init_verify.html",
                        [tfasecret, tfarecoverycodes.split(','), "verify"]))
    else:
        # This shouldn't be reached normally (user intentionally altered action?)
        raise WeasylError("Unexpected")


@login_required
def tfa_disable_get_(request):
    # Return an error if 2FA is not enabled (there's nothing to do in this route)
    _error_if_2fa_is_not_enabled(request.userid)

    return Response(define.webpage(request.userid, "control/2fa/disable.html",
                    [define.get_display_name(request.userid), None]))


@login_required
@token_checked
def tfa_disable_post_(request):
    # Return an error if 2FA is not enabled (there's nothing to do in this route)
    _error_if_2fa_is_not_enabled(request.userid)

    tfaresponse = request.params['tfaresponse']
    verify_checkbox = request.params['verify']
    action = request.params['action']

    if action == "disable" and verify_checkbox:
        # If 2FA was successfully deactivated... return to 2FA dashboard
        if tfa.deactivate(request.userid, tfaresponse):
            raise HTTPSeeOther(location="/control/2fa/status")
        else:
            return Response(define.webpage(request.userid, "control/2fa/disable.html",
                            [define.get_display_name(request.userid), "2fa"]))
    # The user didn't check the verification checkbox (despite HTML5's client-side check)
    elif action == "disable" and not verify_checkbox:
        return Response(define.webpage(request.userid, "control/2fa/disable.html",
                        [define.get_display_name(request.userid), "verify"]))
    else:
        # This shouldn't be reached normally (user intentionally altered action?)
        raise WeasylError("Unexpected")


@login_required
def tfa_generate_recovery_codes_get_(request):
    # Return an error if 2FA is not enabled (there's nothing to do in this route)
    _error_if_2fa_is_not_enabled(request.userid)

    return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
        tfa.generate_recovery_codes(),
        None
    ]))


@login_required
@token_checked
def tfa_generate_recovery_codes_post_(request):
    # Return an error if 2FA is not enabled (there's nothing to do in this route)
    _error_if_2fa_is_not_enabled(request.userid)

    # Extract parameters from the form
    action = request.params['action']
    verify_checkbox = request.params['verify']
    tfaresponse = request.params['tfaresponse']
    tfarecoverycodes = request.params['tfarecoverycodes']

    # Does the user want to save the new recovery codes?
    if action == "save" and verify_checkbox:
        if tfa.verify(request.userid, tfaresponse, consume_recovery_code=False):
            if tfa.store_recovery_codes(request.userid, tfarecoverycodes):
                # Successfuly stored new recovery codes.
                raise HTTPSeeOther(location="/control/2fa/status")
            else:
                # Recovery code string was corrupted or otherwise altered.
                raise WeasylError("Unexpected")
        else:
            return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
                tfarecoverycodes.split(','),
                "2fa"
            ]))
    elif action == "save" and not verify_checkbox:
        return Response(define.webpage(request.userid, "control/2fa/generate_recovery_codes.html", [
            tfarecoverycodes.split(','),
            "verify"
        ]))
    else:
        # This shouldn't be reached normally (user intentionally altered action?)
        raise WeasylError("Unexpected")

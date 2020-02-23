from __future__ import absolute_import

import json
from pyramid.response import Response

from libweasyl import staff

from weasyl import define, errorcode, two_factor_auth
import weasyl.api
from weasyl.error import WeasylError

"""
Contains decorators for weasyl view callables to enforce permissions and the like.
"""


def login_required(view_callable):
    def inner(request):
        if request.userid == 0:
            raise WeasylError('unsigned')
        return view_callable(request)
    return inner


def guest_required(view_callable):
    def inner(request):
        if request.userid != 0:
            raise WeasylError('signed')
        return view_callable(request)
    return inner


def moderator_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('permission')
        if request.userid not in staff.MODS:
            raise WeasylError('permission')
        return view_callable(request)
    return login_required(inner)


def admin_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('permission')
        if request.userid not in staff.ADMINS:
            raise WeasylError('permission')
        return view_callable(request)
    return login_required(inner)


def director_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('permission')
        if request.userid not in staff.DIRECTORS:
            raise WeasylError('permission')
        return view_callable(request)
    return login_required(inner)


def disallow_api(view_callable):
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('permission')
        return view_callable(request)
    return inner


def twofactorauth_enabled_required(view_callable):
    """
    This decorator requires that 2FA be enabled for a given Weasyl account as identified
    by ``request.userid``.
    """
    def inner(request):
        if not two_factor_auth.is_2fa_enabled(request.userid):
            raise WeasylError("TwoFactorAuthenticationRequireEnabled")
        return view_callable(request)
    return inner


def twofactorauth_disabled_required(view_callable):
    """
    This decorator requires that 2FA be disabled for a given Weasyl account as identified
    by ``request.userid``.
    """
    def inner(request):
        if two_factor_auth.is_2fa_enabled(request.userid):
            raise WeasylError("TwoFactorAuthenticationRequireDisbled")
        return view_callable(request)
    return inner


def token_checked(view_callable):
    def inner(request):
        if not weasyl.api.is_api_user(request) and not define.is_csrf_valid(request, request.params.get('token')):
            raise WeasylError('token')
        return view_callable(request)
    return inner


def supports_json(view_callable):
    def inner(request):
        if request.params.get('format', "") == "json":

            try:
                result = view_callable(request)
            except WeasylError as e:
                result = {"error": e.value, "message": errorcode.error_messages.get(e.value)}

            return Response(json.dumps(result), headerlist=[("Content-Type", "application/json")])
        return view_callable(request)
    return inner

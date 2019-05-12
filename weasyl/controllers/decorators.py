from __future__ import absolute_import

import anyjson as json
from pyramid.httpexceptions import HTTPForbidden
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
            return Response(define.webpage(request.userid))
        return view_callable(request)
    return inner


def guest_required(view_callable):
    def inner(request):
        if request.userid != 0:
            return Response(define.webpage(request.userid))
        return view_callable(request)
    return inner


def moderator_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise HTTPForbidden
        if request.userid not in staff.MODS:
            return Response(define.errorpage(request.userid, errorcode.permission))
        return view_callable(request)
    return login_required(inner)


def admin_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise HTTPForbidden
        if request.userid not in staff.ADMINS:
            return Response(define.errorpage(request.userid, errorcode.permission))
        return view_callable(request)
    return login_required(inner)


def director_only(view_callable):
    """Implies login_required."""
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise HTTPForbidden
        if request.userid not in staff.DIRECTORS:
            return Response(define.errorpage(request.userid, errorcode.permission))
        return view_callable(request)
    return login_required(inner)


def disallow_api(view_callable):
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise HTTPForbidden
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
            raise WeasylError("TwoFactorAuthenticationRequireDisabled")
        return view_callable(request)
    return inner


def token_checked(view_callable):
    def inner(request):
        if not weasyl.api.is_api_user(request) and not define.is_csrf_valid(request, request.params.get('token')):
            return Response(define.errorpage(request.userid, errorcode.token), status=403)
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


def rate_limit_route(expiration_time=60 * 2, limit=5):
    """
    A route decorator which enables rate limiting via the rate-limiting middleware tween.

    Adds (or overwrites, if for some reason the client sets them) headers for how long the rate limit block period on
    that route should be, and what the upper-bound of the failed attempts should be.

    :param expiration_time: An integer in seconds representing how long before the rate limit should expire.
        Defaults to 120 (two minutes).
    :param limit: How many attempts are permitted before the rate limit is hit. Default 5.
    :return: The pyramid view_callable/request.
    """
    def outer(view_callable):
        def inner(request):
            request.headers['Wzl-RateLimit-Expiration'] = expiration_time
            request.headers['Wzl-RateLimit-Count'] = limit
            return view_callable(request)
        return inner
    return outer


class controller_base(object):
    """Temporary class to make incremental re-implementation easier."""
    # TODO: Delete this.
    pass

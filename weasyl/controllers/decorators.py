from functools import wraps

from pyramid.response import Response

from libweasyl import staff

from weasyl import define, errorcode, two_factor_auth
import weasyl.api
from weasyl.error import WeasylError

"""
Contains decorators for weasyl view callables to enforce permissions and the like.
"""


csrf_defined: set[tuple[str, str]] = set()


def login_required(view_callable):
    @wraps(view_callable)
    def inner(request):
        if request.userid == 0:
            raise WeasylError('unsigned')
        return view_callable(request)
    return inner


def guest_required(view_callable):
    @wraps(view_callable)
    def inner(request):
        if request.userid != 0:
            raise WeasylError('signed')
        return view_callable(request)
    return inner


def moderator_only(view_callable):
    """Implies login_required."""
    @wraps(view_callable)
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('InsufficientPermissions')
        if request.userid not in staff.MODS:
            raise WeasylError('InsufficientPermissions')
        return view_callable(request)
    return login_required(inner)


def admin_only(view_callable):
    """Implies login_required."""
    @wraps(view_callable)
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('InsufficientPermissions')
        if request.userid not in staff.ADMINS:
            raise WeasylError('InsufficientPermissions')
        return view_callable(request)
    return login_required(inner)


def director_only(view_callable):
    """Implies login_required."""
    @wraps(view_callable)
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('InsufficientPermissions')
        if request.userid not in staff.DIRECTORS:
            raise WeasylError('InsufficientPermissions')
        return view_callable(request)
    return login_required(inner)


def disallow_api(view_callable):
    @wraps(view_callable)
    def inner(request):
        if weasyl.api.is_api_user(request):
            raise WeasylError('InsufficientPermissions')
        return view_callable(request)
    return inner


def twofactorauth_enabled_required(view_callable):
    """
    This decorator requires that 2FA be enabled for a given Weasyl account as identified
    by ``request.userid``.
    """
    @wraps(view_callable)
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
    @wraps(view_callable)
    def inner(request):
        if two_factor_auth.is_2fa_enabled(request.userid):
            raise WeasylError("TwoFactorAuthenticationRequireDisbled")
        return view_callable(request)
    return inner


def csrf_skip(view_callable):
    key = (view_callable.__module__, view_callable.__qualname__)

    if key in csrf_defined:
        raise RuntimeError(f"multiple CSRF policies for {key}")  # pragma: no cover

    csrf_defined.add(key)

    return view_callable


def token_checked(view_callable):
    csrf_skip(view_callable)

    @wraps(view_callable)
    def inner(request):
        assert request.method in ("POST", "DELETE", "PUT", "PATCH")
        if not weasyl.api.is_api_user(request) and not define.is_csrf_valid(request):
            raise WeasylError('token')
        return view_callable(request)
    return inner


def supports_json(view_callable):
    @wraps(view_callable)
    def inner(request):
        if request.params.get('format', "") == "json":

            try:
                result = view_callable(request)
            except WeasylError as e:
                result = {"error": e.value, "message": errorcode.error_messages.get(e.value)}

            return Response(json=result)
        return view_callable(request)
    return inner

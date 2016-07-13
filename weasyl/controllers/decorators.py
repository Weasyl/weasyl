import anyjson as json
from pyramid.httpexceptions import HTTPForbidden
from pyramid.response import Response

from libweasyl import staff

from weasyl import define, errorcode
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
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        if request.userid not in staff.MODS:
            return Response(define.errorpage(request.userid, errorcode.permission))
        return view_callable(request)
    return inner


def admin_only(view_callable):
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        if request.userid not in staff.ADMINS:
            return Response(define.errorpage(request.userid, errorcode.permission))
        return view_callable(request)
    return inner


def disallow_api(view_callable):
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        return view_callable(request)
    return inner


def token_checked(view_callable):
    def inner(request):
        if not weasyl.api.is_api_user() and request.params.get('token', "") != define.get_token():
            return Response(define.errorpage(request.userid, errorcode.token))
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


class controller_base(object):
    """Temporary class to make incremental re-implementation easier."""
    # TODO: Delete this.
    pass

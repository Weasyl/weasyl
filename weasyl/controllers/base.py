from pyramid.httpexceptions import HTTPForbidden
from pyramid.response import Response

from libweasyl import staff

from weasyl import define, errorcode
import weasyl.api


"""
Contains decorators for weasyl view callables to enforce permissions and the like.
"""


def status_check(view_callable):
    # Should be used universally as the first decorator.
    def inner(request):
        userid = define.get_userid()
        status = define.common_status_check(userid)
        if status:
            return Response(define.common_status_page(userid, status))
        return view_callable(request)
    return inner


def login_required(view_callable):
    def inner(request):
        userid = define.get_userid()
        if userid == 0:
            return Response(define.webpage(userid))
        return view_callable(request)
    return inner


def guest_required(view_callable):
    def inner(request):
        userid = define.get_userid()
        if userid != 0:
            return Response(define.webpage(userid))
        return view_callable(request)
    return inner


def moderator_only(view_callable):
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        userid = define.get_userid()
        if userid not in staff.MODS:
            return Response(define.errorpage(userid, errorcode.permission))
        return view_callable(request)
    return inner


def admin_only(view_callable):
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        userid = define.get_userid()
        if userid not in staff.ADMINS:
            return Response(define.errorpage(userid, errorcode.permission))
        return view_callable(request)
    return inner


def disallow_api(view_callable):
    def inner(request):
        if weasyl.api.is_api_user():
            raise HTTPForbidden
        return view_callable(request)
    return inner

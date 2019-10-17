

from pyramid.response import Response

from weasyl import define


def halloweasyl2014_(request):
    return Response(define.webpage(userid=request.userid, template='events/halloweasyl.html'))

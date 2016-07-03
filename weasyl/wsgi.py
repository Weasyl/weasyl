from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from web.utils import storify

from libweasyl.configuration import configure_libweasyl
from weasyl.media import format_media_link
import weasyl.define as d
import weasyl.macro as m
import weasyl.middleware as mw
import weasyl.controllers.routes


config = Configurator()

config.add_tween("weasyl.middleware.session_tween_factory")
config.add_tween("weasyl.middleware.db_timer_tween_factory")
config.add_tween("weasyl.middleware.property_tween_factory")
config.add_tween("weasyl.middleware.cache_clear_tween_factory")

config.add_route("index", "/")
# Helping me see how slow this is:
import time
start = time.time()
config.scan("weasyl.define")
config.scan("weasyl.controllers")
print "Scanned in %d seconds" % (time.time() - start)


# Set up some exception handling.
def weasyl_404(request):
    userid = d.get_userid()
    return Response(d.errorpage(userid, "**404!** The page you requested could not be found."),
                    status="404 Not Found")

config.add_notfound_view(view=weasyl_404, append_slash=True)
config.add_view(view=mw.weasyl_exception_view, context=Exception)


def web_input(request, **kwargs):
    """
    Callable that processes the pyramid request.params multidict into a web.py storage object
    in the style of web.input().
    TODO: Replace usages of this method with accessing request directly.

    @param request: The pyramid request object.
    @param kwargs: Default values. If a default value is a list, it indicates that multiple
        values of that key should be collapsed into a list.
    @return: A dictionary-like object in the fashion of web.py's web.input()
    """
    return storify(request.params.mixed(), defaults=kwargs)

config.add_request_method(web_input)


wsgi_app = config.make_wsgi_app()


wsgi_app = mw.InputWrapMiddleware(wsgi_app)
wsgi_app = mw.URLSchemeFixingMiddleware(wsgi_app)
if d.config_read_bool('profile_responses', section='backend'):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    wsgi_app = ProfilerMiddleware(
        wsgi_app, profile_dir=m.MACRO_SYS_BASE_PATH + 'profile-stats')
if d.config_obj.has_option('sentry', 'dsn'):
    wsgi_app = mw.SentryEnvironmentMiddleware(wsgi_app, d.config_obj.get('sentry', 'dsn'))


configure_libweasyl(
    dbsession=d.sessionmaker,
    not_found_exception=HTTPNotFound,
    base_file_path=m.MACRO_SYS_BASE_PATH,
    staff_config_path=m.MACRO_SYS_STAFF_CONFIG_PATH,
    media_link_formatter_callback=format_media_link,
)

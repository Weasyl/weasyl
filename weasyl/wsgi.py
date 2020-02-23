from __future__ import absolute_import

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound

from libweasyl.configuration import configure_libweasyl
from weasyl.controllers.routes import setup_routes_and_views
import weasyl.define as d
import weasyl.macro as m
from weasyl.media import format_media_link
import weasyl.middleware as mw
from weasyl import staff_config
from weasyl import template


# Get a configurator and register some tweens to handle cleanup, etc.
config = Configurator()
config.add_tween("weasyl.middleware.status_check_tween_factory")
config.add_tween("weasyl.middleware.sql_debug_tween_factory")
config.add_tween("weasyl.middleware.session_tween_factory")
config.add_tween("weasyl.middleware.db_timer_tween_factory")
config.add_tween("weasyl.middleware.cache_clear_tween_factory")
config.add_tween("weasyl.middleware.database_session_cleanup_tween_factory")
config.add_tween("weasyl.middleware.http2_server_push_tween_factory")
config.add_tween("pyramid.tweens.excview_tween_factory")  # Required to catch exceptions thrown in tweens.


def setup_jinja2_env():
    env = config.get_jinja2_environment()
    env.filters.update(template.filters)
    env.globals.update(template.jinja2_globals)
    env.add_extension('jinja2.ext.do')


config.include('pyramid_jinja2')
config.add_jinja2_search_path('weasyl:templates/', name='.jinja2')
config.action(None, setup_jinja2_env, order=999)

# Set up some exception handling and all our views.
def weasyl_404(request):
    request.response.status = 404
    return {'error': "**404!** The page you requested could not be found."}


config.add_notfound_view(view=weasyl_404, append_slash=True, renderer='/error/error.jinja2')
config.add_view(view=mw.weasyl_exception_view, context=Exception, renderer='/error/error.jinja2')

setup_routes_and_views(config)


# Setup properties and methods for request objects.
config.add_request_method(mw.pg_connection_request_property, name='pg_connection', reify=True)
config.add_request_method(mw.userid_request_property, name='userid', reify=True)
config.add_request_method(mw.log_exc_request_method, name='log_exc')
config.add_request_method(mw.web_input_request_method, name='web_input')
config.add_request_method(mw.set_cookie_on_response)
config.add_request_method(mw.delete_cookie_on_response)


wsgi_app = config.make_wsgi_app()
wsgi_app = mw.InputWrapMiddleware(wsgi_app)
wsgi_app = mw.URLSchemeFixingMiddleware(wsgi_app)
if d.config_read_bool('profile_responses', section='backend'):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    wsgi_app = ProfilerMiddleware(
        wsgi_app, profile_dir=m.MACRO_STORAGE_ROOT + 'profile-stats')
if d.config_obj.has_option('sentry', 'dsn'):
    wsgi_app = mw.SentryEnvironmentMiddleware(wsgi_app, d.config_obj.get('sentry', 'dsn'))


configure_libweasyl(
    dbsession=d.sessionmaker,
    not_found_exception=HTTPNotFound,
    base_file_path=m.MACRO_STORAGE_ROOT,
    staff_config_dict=staff_config.load(),
    media_link_formatter_callback=format_media_link,
)

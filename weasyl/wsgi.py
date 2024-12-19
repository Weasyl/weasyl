from prometheus_client import (
    CollectorRegistry,
    multiprocess,
)
from prometheus_client.openmetrics import exposition as openmetrics
from pyramid.config import Configurator
from pyramid.response import Response

from libweasyl import cache
from libweasyl.configuration import configure_libweasyl
from weasyl.cache import RequestMemcachedStats
from weasyl.controllers.routes import setup_routes_and_views
import weasyl.define as d
import weasyl.macro as m
from weasyl.config import config_read_bool, config_read_setting
from weasyl.media import format_media_link
import weasyl.middleware as mw
from weasyl import staff_config


# Get a configurator and register some tweens to handle cleanup, etc.
config = Configurator(
    request_factory=mw.Request,
)
config.add_tween("weasyl.middleware.status_check_tween_factory")
config.add_tween("weasyl.middleware.session_tween_factory")
config.add_tween("weasyl.middleware.db_timer_tween_factory")
config.add_tween("weasyl.middleware.cache_clear_tween_factory")
config.add_tween("weasyl.middleware.database_session_cleanup_tween_factory")
config.add_tween("weasyl.middleware.preload_tween_factory")
config.add_tween("weasyl.middleware.query_debug_tween_factory")
config.add_tween("pyramid.tweens.excview_tween_factory")  # Required to catch exceptions thrown in tweens.
config.add_tween("weasyl.middleware.utf8_path_tween_factory")


# Set up some exception handling and all our views.
def weasyl_404(request):
    userid = d.get_userid()
    return Response(d.errorpage(userid, "**404!** The page you requested could not be found."),
                    status="404 Not Found")


config.add_notfound_view(view=weasyl_404, append_slash=True)
config.add_view(view=mw.weasyl_exception_view, context=Exception, exception_only=True)

setup_routes_and_views(config)


# Setup properties and methods for request objects.
config.add_request_method(mw.pg_connection_request_property, name='pg_connection', reify=True)
config.add_request_method(mw.userid_request_property, name='userid', reify=True)
config.add_request_method(mw.web_input_request_method, name='web_input')


def make_wsgi_app(*, configure_cache=True):
    wsgi_app = config.make_wsgi_app()

    if config_read_bool('profile_responses', section='backend'):
        from werkzeug.middleware.profiler import ProfilerMiddleware
        wsgi_app = ProfilerMiddleware(
            wsgi_app,
            stream=None,
            profile_dir=m.MACRO_STORAGE_ROOT + 'profile-stats',
        )

    configure_libweasyl(
        dbsession=d.sessionmaker,
        base_file_path=m.MACRO_STORAGE_ROOT,
        staff_config_dict=staff_config.load(),
        media_link_formatter_callback=format_media_link,
    )

    if configure_cache:
        cache.JsonPylibmcBackend.register()
        cache.region.configure(
            'libweasyl.cache.pylibmc',
            arguments={
                'url': config_read_setting('servers', "127.0.0.1", section='memcached').split(),
                'binary': True,
                'behaviors': {
                    'tcp_nodelay': True,
                },
            },
            wrap=[cache.ThreadCacheProxy, RequestMemcachedStats],
            replace_existing_backend=True
        )

    def app_with_metrics(environ, start_response):
        if environ["PATH_INFO"] == "/metrics":
            if "HTTP_X_FORWARDED_FOR" in environ:
                start_response("403 Forbidden", [])
                return []

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            data = openmetrics.generate_latest(registry)

            start_response("200 OK", [
                ("Content-Type", openmetrics.CONTENT_TYPE_LATEST),
                ("Content-Length", str(len(data))),
            ])
            return [data]

        return wsgi_app(environ, start_response)

    return app_with_metrics

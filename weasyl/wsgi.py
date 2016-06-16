import web

from libweasyl.configuration import configure_libweasyl
from weasyl.media import format_media_link
import weasyl.define as d
import weasyl.macro as m
import weasyl.middleware as mw
import weasyl.controllers.urls

web.config.debug = False
app = web.application(weasyl.controllers.urls.controllers, globals())

app.add_processor(mw.cache_clear_processor)
app.add_processor(mw.db_connection_processor)
app.add_processor(mw.db_timer_processor(app))
app.add_processor(mw.session_processor)

# I'd use @app.add_processor for this, but web.py doesn't allow exceptions
# raised by app code to propagate to processors. so, I have to reach my paws
# into its filty rectum and yank this method out.
mw._handle = app.handle

# and jam this method back in.
app.handle = mw.weasyl_exception_processor

# similarly for this; web.py doesn't expose the endpoint name anywhere, so we
# force it to.
mw._delegate = app._delegate
app._delegate = mw.endpoint_recording_delegate


def weasyl_404():
    userid = d.get_userid()
    return web.notfound(d.errorpage(
        userid, "**404!** The page you requested could not be found."))

app.notfound = weasyl_404


wsgi_app = app.wsgifunc()
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
    not_found_exception=web.notfound,
    base_file_path=m.MACRO_SYS_BASE_PATH,
    staff_config_dict=m.MACRO_SYS_STAFF_CONFIG,
    media_link_formatter_callback=format_media_link,
)

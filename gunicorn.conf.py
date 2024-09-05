from gunicorn.glogging import CONFIG_DEFAULTS as _LOGCONFIG_DEFAULTS
from prometheus_client import multiprocess


wsgi_app = "weasyl.wsgi:make_wsgi_app()"

proc_name = "weasyl"

preload_app = False

secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}
forwarded_allow_ips = '*'

logconfig_dict = {
    "loggers": {
        **_LOGCONFIG_DEFAULTS["loggers"],
        "weasyl": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)

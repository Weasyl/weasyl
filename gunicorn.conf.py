from prometheus_client import multiprocess


wsgi_app = "weasyl.wsgi:make_wsgi_app()"

proc_name = "weasyl"

preload_app = False

secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}
forwarded_allow_ips = '*'


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)

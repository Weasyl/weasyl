wsgi_app = "weasyl.wsgi:make_wsgi_app()"

proc_name = "weasyl"

preload_app = True

secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}
forwarded_allow_ips = '*'

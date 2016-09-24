from __future__ import absolute_import

from webtest import TestApp

from weasyl.wsgi import wsgi_app


app = TestApp(wsgi_app)

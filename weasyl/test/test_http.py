

import pytest

from weasyl import http


@pytest.mark.parametrize(('wsgi_env', 'expected'), [
    ({}, {}),
    ({'PATH_INFO': '/search', 'QUERY_STRING': 'q=example'}, {}),
    ({'HTTP_ACCEPT': '*/*'}, {'Accept': '*/*'}),
    (
        {'CONTENT_LENGTH': '', 'HTTP_ACCEPT_ENCODING': 'gzip', 'HTTP_UPGRADE_INSECURE_REQUESTS': '1'},
        {'Accept-Encoding': 'gzip', 'Upgrade-Insecure-Requests': '1'},
    ),
])
def test_get_headers(wsgi_env, expected):
    assert http.get_headers(wsgi_env) == expected

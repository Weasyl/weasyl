import pytest

from weasyl import define
from weasyl.test import db_utils


@pytest.mark.usefixtures("db", "cache")
def test_sfw_toggle(app, monkeypatch):
    monkeypatch.setattr(define, "ORIGIN", "http://localhost")

    user = db_utils.create_user()
    app.set_cookie(*db_utils.create_session(user).split("=", 1))

    resp = app.post("/control/sfwtoggle", {
        "redirect": "/~referer",
    }, status=303)
    assert resp.headers["location"] == "http://localhost/~referer", "SFW toggle should redirect back to original page"

    resp = app.post("/control/sfwtoggle", {
        "redirect": "//evil.example/",
    }, status=303)
    assert resp.headers["location"] == "http://localhost//evil.example/", "SFW toggle shouldn’t act as an open redirect"

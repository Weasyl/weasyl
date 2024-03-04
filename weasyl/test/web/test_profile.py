from contextlib import contextmanager

import arrow
import pytest

from weasyl.test import db_utils


@contextmanager
def _guest(app):
    old_cookiejar = list(app.cookiejar)

    app.reset()

    yield

    for cookie in old_cookiejar:
        app.cookiejar.set_cookie(cookie)


def _find_form(resp, *, action):
    [form] = (form for form in resp.forms.values() if form.action == action)
    return form


@pytest.mark.usefixtures("db", "cache")
def test_age_set_and_display(app):
    birthdate = arrow.utcnow().shift(years=-18, months=-1)

    user = db_utils.create_user(username="profiletest")

    resp = app.get("/~profiletest")
    assert resp.html.find(id="user-id").text.strip() == ""

    app.set_cookie(*db_utils.create_session(user).split("=", 1))

    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")

    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (False, "", "")

    form["birthdate-month"].value = birthdate.month
    form["birthdate-year"].value = birthdate.year
    form.submit()

    resp = app.get("/control/editprofile")
    fresh_form = _find_form(resp, action="/control/editprofile")
    assert (fresh_form["show_age"].checked, fresh_form["birthdate-month"].value, fresh_form["birthdate-year"].value) == (False, "", ""), "birthdate isn’t set when option to show age isn’t checked"

    form = fresh_form
    form["show_age"].checked = True
    form.submit()

    resp = app.get("/control/editprofile")
    fresh_form = _find_form(resp, action="/control/editprofile")
    assert (fresh_form["show_age"].checked, fresh_form["birthdate-month"].value, fresh_form["birthdate-year"].value) == (False, "", ""), "option to show age isn’t set when birthdate isn’t provided"

    form["birthdate-month"].value = birthdate.month
    form["birthdate-year"].value = birthdate.year
    form.submit()

    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (True, str(birthdate.month), str(birthdate.year))
    assert resp.html.find("fieldset", id="birthdate").has_attr("disabled"), "birthdate can’t be changed in UI once set"

    with _guest(app):
        resp = app.get("/~profiletest")
        assert resp.html.find(id="user-id").text.strip() == "18"

    form["show_age"].checked = False
    form.submit()

    # option to show age can be unset
    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (False, str(birthdate.month), str(birthdate.year))

    with _guest(app):
        resp = app.get("/~profiletest")
        assert resp.html.find(id="user-id").text.strip() == ""

    form["show_age"].checked = True
    form["birthdate-month"] = 1
    form["birthdate-year"] = 1990
    form.submit()
    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (True, str(birthdate.month), str(birthdate.year)), "birthdate can’t be changed once set"

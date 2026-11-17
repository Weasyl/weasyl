import datetime
from contextlib import contextmanager

import arrow
import pytest
import webtest

from weasyl.errorcode import error_messages
from weasyl.test import db_utils
from weasyl.test.web.common import create_visual
from weasyl.test.web.common import read_asset
from weasyl.test.web.test_characters import create_character
from weasyl.test.web.test_journals import create_journal


@contextmanager
def _guest(app):
    old_cookiejar = list(app.cookiejar)

    app.reset()

    yield

    for cookie in old_cookiejar:
        app.cookiejar.set_cookie(cookie)


def _find_form(resp, *, action):
    [form] = (form for key, form in resp.forms.items() if isinstance(key, int) and form.action == action)
    return form


@pytest.mark.usefixtures("db", "cache")
def test_age_set_and_display(app):
    birthdate = arrow.utcnow().shift(years=-18, months=-1)

    user = db_utils.create_user(username="profiletest")

    resp = app.get("/~profiletest")
    assert resp.html.find(id="user-id").text.strip() == "profiletest"

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
        assert resp.html.find(id="user-id").text.split() == ["profiletest", "/", "18"]

    form["show_age"].checked = False
    form.submit()

    # option to show age can be unset
    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (False, str(birthdate.month), str(birthdate.year))

    with _guest(app):
        resp = app.get("/~profiletest")
        assert resp.html.find(id="user-id").text.strip() == "profiletest"

    form["show_age"].checked = True
    form["birthdate-month"] = 1
    form["birthdate-year"] = 1990
    form.submit()
    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    assert (form["show_age"].checked, form["birthdate-month"].value, form["birthdate-year"].value) == (True, str(birthdate.month), str(birthdate.year)), "birthdate can’t be changed once set"


def _get_birthdate_under_age(age: int) -> datetime.date:
    # `days=4`: A test run sufficiently late on February 28 (UTC) in a non-leap year needs to produce April, not March, since it could already be March in the most advanced time zone.
    return arrow.utcnow().shift(years=-age, months=1, days=4).date()


@pytest.mark.usefixtures("db", "cache")
def test_age_terms(app):
    u13_birthdate = _get_birthdate_under_age(13)

    user = db_utils.create_user(username="profiletest")
    app.set_cookie(*db_utils.create_session(user).split("=", 1))

    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    form["show_age"].checked = True
    form["birthdate-month"].value = u13_birthdate.month
    form["birthdate-year"].value = u13_birthdate.year

    resp = form.submit(expect_errors=True)
    assert resp.status_int == 422, "can’t display age under 13"
    assert resp.html.find(id="error_content").p.text.strip() == error_messages["birthdayInconsistentWithTerms"]

    with _guest(app):
        resp = app.get("/~profiletest")
        assert resp.html.find(id="user-id").text.strip() == "profiletest"


def _create_submission(app, user, **kwargs):
    return create_visual(
        app,
        user,
        submitfile=webtest.Upload("wesley1.png", read_asset("img/wesley1.png"), "image/png"),
        **kwargs,
    )


def _edit_submission(app, user):
    submitid = _create_submission(app, user, rating="10")
    resp = (
        app.get(f"/submission/{submitid}")
        .maybe_follow()
        .click("Edit Submission Details")
    )
    form = _find_form(resp, action="/edit/submission")
    form["rating"] = "30"
    form.submit(status=303)


def _edit_character(app, user):
    charid = create_character(app, user, rating="10")
    resp = (
        app.get(f"/character/{charid}")
        .click("Edit Character Details")
    )
    form = _find_form(resp, action="/edit/character")
    form["rating"] = "30"
    form.submit(status=303)


def _edit_journal(app, user):
    resp = (
        create_journal(app, user, rating="10")
        .follow()
        .click("Edit Journal Details")
    )
    form = _find_form(resp, action="/edit/journal")
    form["rating"] = "30"
    form.submit(status=303)


def _assert_adult_params(type_name, create, edit):
    return [
        pytest.param(lambda app, user: create(app, user, rating="10"), False, id=f"create-{type_name}-rating-general"),
        pytest.param(lambda app, user: create(app, user, rating="30"), True, id=f"create-{type_name}-rating-mature"),
        pytest.param(edit, True, id=f"edit-{type_name}-rating-mature"),
    ]


@pytest.mark.usefixtures("db", "cache")
@pytest.mark.parametrize(("user_action", "expect_assertion"), [
    pytest.param(None, False, id="noop"),
    *_assert_adult_params("submission", _create_submission, _edit_submission),
    *_assert_adult_params("character", create_character, _edit_character),
    *_assert_adult_params("journal", create_journal, _edit_journal),
])
def test_assert_adult(app, user_action, expect_assertion):
    u18_birthdate = _get_birthdate_under_age(18)

    forward_user = db_utils.create_user(username="forwarduser")
    app.set_cookie(*db_utils.create_session(forward_user).split("=", 1))

    if user_action is not None:
        user_action(app, forward_user)

    resp = app.get("/control/editprofile")
    form = _find_form(resp, action="/control/editprofile")
    form["show_age"].checked = True
    form["birthdate-month"].value = u18_birthdate.month
    form["birthdate-year"].value = u18_birthdate.year

    if expect_assertion:
        resp = form.submit(expect_errors=True)
        assert resp.status_int == 422, "can’t display age under 18 after using age-restricted ratings"
        assert resp.html.find(id="error_content").p.text.strip() == error_messages["birthdayInconsistentWithRating"]

        with _guest(app):
            resp = app.get("/~forwarduser")
            assert resp.html.find(id="user-id").text.strip() == "forwarduser"
    else:
        resp = form.submit()
        assert resp.status_int == 303, "can display age under 18 after not using age-restricted ratings"

        with _guest(app):
            resp = app.get("/~forwarduser")
            assert resp.html.find(id="user-id").text.split() == ["forwarduser", "/", "17"]


@pytest.mark.usefixtures("db", "cache")
@pytest.mark.parametrize(("site_names", "site_values", "rel_me_expected"), [
    ("Bluesky", "weasyl.invalid", True),
    ("Email", "weasyl@weasyl.invalid", False),
    ("Something non-default", "not a URL", False),
    ("Something non-default", "https://weasyl.invalid/", True),
])
def test_profile_links_rel_me(app, site_names: str, site_values: str, rel_me_expected: bool):
    user = db_utils.create_user(username="profiletest")
    app.set_cookie(*db_utils.create_session(user).split("=", 1))

    app.post("/control/editprofile", {
        # Unrelated, but necessary for successful form submission
        "set_commish": "e",
        "set_request": "e",
        "set_trade": "e",

        "site_names": site_names,
        "site_values": site_values,
    })

    resp = app.get("/~profiletest")
    assert resp.html.find(string=site_names)
    assert resp.html.find(string=site_values)

    rel = resp.html.find(string=site_values).parent.get("rel", [])
    assert ("me" in rel) is rel_me_expected

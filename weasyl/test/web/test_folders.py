from __future__ import absolute_import

import pytest

from weasyl.test import db_utils


@pytest.mark.usefixtures("db")
def test_create_folders(app):
    user = db_utils.create_user(username="foldertest")
    app.set_cookie(*db_utils.create_session(user).split("=", 1))

    resp = app.get("/manage/folders")
    form = resp.forms["create-folder"]

    form["title"] = "Test folder 1"
    form["parentid"] = "0"
    form.submit()

    form["title"] = "Test folder 3"
    form.submit()

    form["title"] = "Test folder 1.2"
    form.submit()

    form["title"] = "Test folder 2"
    form.submit()

    resp = app.get("/manage/folders")
    form = resp.forms["create-folder"]

    form["title"] = "Test folder 1.1"
    form["parentid"].select(text="Test folder 1")
    form.submit()

    resp = app.get("/manage/folders")
    form = resp.forms["move-folder"]

    form["folderid"].select(text="Test folder 1.2")
    form["parentid"].select(text="Test folder 1")
    form.submit()

    resp = app.get("/submissions/foldertest")
    folders = resp.html.find("h3", string="Folders").find_next_siblings("p")
    assert len(folders) == 5
    assert folders[0].get("style") is None and folders[0].text == "Test folder 1"
    assert folders[1].get("style") == "margin-left:15px;" and folders[1].text == "Test folder 1.1"
    assert folders[2].get("style") == "margin-left:15px;" and folders[2].text == "Test folder 1.2"
    assert folders[3].get("style") is None and folders[3].text == "Test folder 2"
    assert folders[4].get("style") is None and folders[4].text == "Test folder 3"

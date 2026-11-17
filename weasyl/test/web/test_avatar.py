import pytest
from webtest.forms import Upload

from weasyl.test import db_utils
from weasyl.test.web.common import (
    fingerprint,
    read_asset,
    read_storage,
)


@pytest.mark.usefixtures('db', 'cache')
def test_animated_gif_and_clear(app, submission_user):
    app.set_cookie(*db_utils.create_session(submission_user).split("=", 1))

    form = app.get('/manage/avatar').forms['upload-avatar']
    form['image'] = Upload('loader.gif', read_asset('img/loader.gif'), 'image/gif')
    resp = form.submit().follow()
    resp = resp.forms['manage-avatar'].submit().follow()
    avatar_url = resp.html.find(id='avatar')['src']

    assert fingerprint(read_storage(avatar_url)) == (6034, "246d5bb3bcdd9d9a727e5db171d3d4965d545fe52475bb9f1d153bf67b57")

    form = app.get('/manage/avatar').forms['upload-avatar']
    form['image'] = None
    resp = form.submit().follow()
    avatar_url = resp.html.find(id='avatar')['src']

    assert avatar_url.startswith('/img/default-avatar-')

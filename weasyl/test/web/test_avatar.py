import pytest
from PIL import Image
from webtest.forms import Upload

from weasyl.test import db_utils
from weasyl.test.web.common import (
    get_storage_path,
    read_asset,
)


@pytest.mark.usefixtures('db', 'cache')
def test_animated_gif_and_clear(app, submission_user):
    app.set_cookie(*db_utils.create_session(submission_user).split("=", 1))

    form = app.get('/manage/avatar').forms['upload-avatar']
    form['image'] = Upload('loader.gif', read_asset('img/loader.gif'), 'image/gif')
    resp = form.submit().follow()
    resp = resp.forms['manage-avatar'].submit().follow()
    avatar_url = resp.html.find(id='avatar')['src']

    with Image.open(get_storage_path(avatar_url)) as avatar:
        assert avatar.n_frames == 12
        assert avatar.size == (100, 100)

    form = app.get('/manage/avatar').forms['upload-avatar']
    form['image'] = None
    resp = form.submit().follow()
    avatar_url = resp.html.find(id='avatar')['src']

    assert avatar_url.startswith('/img/default-avatar-')

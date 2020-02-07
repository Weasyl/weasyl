# encoding: utf-8
from __future__ import absolute_import, division

import hashlib
from io import BytesIO

import pytest
import webtest

from weasyl.test import db_utils
from weasyl.test.web.common import create_visual, read_static_image, read_storage_image


def _image_hash(image):
    return hashlib.sha224(image.tobytes()).hexdigest()


@pytest.mark.usefixtures('db', 'no_csrf')
def test_visual_reupload_thumbnail_and_cover(app, submission_user):
    # resized to be larger than COVER_SIZE so a cover is created
    with BytesIO() as f:
        read_static_image('images/wesley1.png').resize((2200, 200)).save(f, format='PNG')
        wesley1_large = webtest.Upload('wesley1.png', f.getvalue(), 'image/png')

    with BytesIO() as f:
        read_static_image('images/wesley-jumpingtext.png').resize((2200, 100)).save(f, format='PNG')
        wesley2_large = webtest.Upload('wesley-jumpingtext.png', f.getvalue(), 'image/png')

    cookie = db_utils.create_session(submission_user)

    # Create submission 1 with image 1
    v1 = create_visual(app, submission_user, submitfile=wesley1_large)

    # Reupload submission 1 with image 2
    app.post('/reupload/submission', {
        'targetid': u'%i' % (v1,),
        'submitfile': wesley2_large,
    }, headers={'Cookie': cookie}).follow()

    [thumb] = app.get('/~submissiontest').html.select('#user-thumbs img')
    v1_new_thumbnail_url = thumb['src']
    v1_new_cover_url = app.get('/~submissiontest/submissions/%i/test-title' % (v1,)).html.find(id='detail-art').img['src']

    # Remove submission 1, so uploading a duplicate image is allowed
    app.post('/remove/submission', {
        'submitid': u'%i' % (v1,),
    }, headers={'Cookie': cookie}).follow()

    # Upload submission 2 with image 2
    v2 = create_visual(
        app,
        submission_user,
        submitfile=wesley2_large,
    )

    [thumb] = app.get('/~submissiontest').html.select('#user-thumbs img')
    v2_thumbnail_url = thumb['src']
    v2_cover_url = app.get('/~submissiontest/submissions/%i/test-title' % (v2,)).html.find(id='detail-art').img['src']

    # The reupload of submission 1 should look like submission 2
    assert _image_hash(read_storage_image(v1_new_thumbnail_url)) == _image_hash(read_storage_image(v2_thumbnail_url))
    assert _image_hash(read_storage_image(v2_cover_url)) == _image_hash(read_storage_image(v1_new_cover_url))

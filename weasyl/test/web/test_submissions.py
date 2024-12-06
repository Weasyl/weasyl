import hashlib
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO

import arrow
import pytest
import webtest

from libweasyl import ratings
from weasyl import submission
from weasyl.test import db_utils
from weasyl.test.web.common import (
    BASE_LITERARY_FORM,
    BASE_VISUAL_FORM,
    create_visual,
    get_storage_path,
    read_asset,
    read_asset_image,
    read_storage_image,
)


def _image_hash(image):
    return hashlib.sha224(image.tobytes()).hexdigest()


@pytest.mark.parametrize('age', [17, 19])
@pytest.mark.usefixtures('db')
def test_rating_accessibility(app, age):
    submission_user = db_utils.create_user('submission_test', birthday=arrow.utcnow().shift(years=-age))
    cookie = db_utils.create_session(submission_user)

    def _post_expecting(form, expected_rating):
        success = expected_rating is not None
        resp = app.post('/submit/visual', form, headers={'Cookie': cookie}, status=303 if success else 422)

        if success:
            resp = resp.maybe_follow(headers={'Cookie': cookie})
            assert "Rating: %s" % (expected_rating,) in resp.html.find(id='di-info').dl.text
        else:
            assert resp.html.find(id='error_content').p.text == "The specified rating is invalid."

    form = dict(
        BASE_VISUAL_FORM,
        rating='30',
        submitfile=webtest.Upload('wesley1.png', read_asset('img/wesley1.png'), 'image/png'),
    )
    _post_expecting(form, 'Mature' if age >= 18 else None)

    form['submitfile'] = webtest.Upload('wesley-jumpingtext.png', read_asset('img/help/wesley-jumpingtext.png'), 'image/png')
    form['rating'] = '40'
    _post_expecting(form, 'Explicit' if age >= 18 else None)

    form['submitfile'] = webtest.Upload('wesley-draw.png', read_asset('img/help/wesley-draw.png'), 'image/png')
    form['rating'] = '10'
    _post_expecting(form, 'General')


@pytest.mark.usefixtures('db')
def test_gif_thumbnail_static(app, submission_user):
    create_visual(
        app, submission_user,
        submitfile=webtest.Upload('loader.gif', read_asset('img/loader.gif'), 'image/gif'),
    )

    [thumb_compat] = app.get('/~submissiontest').html.select('#user-thumbs img')
    assert thumb_compat['src'].endswith('.jpg')

    [thumb] = app.get('/~submissiontest').html.select('#user-thumbs .thumb-bounds')
    assert thumb.picture is not None
    assert thumb.picture.source['srcset'].endswith('.webp')


@pytest.mark.usefixtures('db')
def test_visual_reupload_thumbnail_and_cover(app, submission_user):
    # resized to be larger than COVER_SIZE so a cover is created
    with BytesIO() as f:
        read_asset_image('img/wesley1.png').resize((2200, 200)).save(f, format='PNG')
        wesley1_large = webtest.Upload('wesley1.png', f.getvalue(), 'image/png')

    with BytesIO() as f:
        read_asset_image('img/help/wesley-jumpingtext.png').resize((2200, 100)).save(f, format='PNG')
        wesley2_large = webtest.Upload('wesley-jumpingtext.png', f.getvalue(), 'image/png')

    cookie = db_utils.create_session(submission_user)

    # Create submission 1 with image 1
    v1 = create_visual(app, submission_user, submitfile=wesley1_large)

    # Reupload submission 1 with image 2
    app.post('/reupload/submission', {
        'targetid': '%i' % (v1,),
        'submitfile': wesley2_large,
    }, headers={'Cookie': cookie}).follow()

    [thumb] = app.get('/~submissiontest').html.select('#user-thumbs img')
    v1_new_thumbnail_url = thumb['src']
    v1_new_cover_url = app.get('/~submissiontest/submissions/%i/test-title' % (v1,)).html.find(id='detail-art').img['src']

    # Remove submission 1, so uploading a duplicate image is allowed
    app.post('/remove/submission', {
        'submitid': '%i' % (v1,),
    }, headers={'Cookie': cookie}).follow(headers={'Cookie': cookie})

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


@pytest.mark.parametrize('link,normalized', [
    (
        'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
        'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
    ),
    (
        'https://docs.google.com/document/d/zd9LMaQo_rfD-ZUhI1WPDK2nhCI3Z3LmchHpLogIVqCd/pub',
        'https://docs.google.com/document/d/zd9LMaQo_rfD-ZUhI1WPDK2nhCI3Z3LmchHpLogIVqCd/pub?embedded=true',
    ),
    (
        'docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub',
        'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
    ),
    (
        '<iframe src="https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true"></iframe>',
        'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
    ),
    (
        'javascript:alert(1)//https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
        'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr14/pub?embedded=true',
    ),
    (
        'https://docs.google.com/document/d/e/1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli/edit?usp=sharing',
        None,
    ),
])
@pytest.mark.usefixtures('db')
def test_google_docs_embed_create(app, submission_user, link, normalized):
    app.set_cookie(*db_utils.create_session(submission_user).split("=", 1))

    form = {
        **BASE_LITERARY_FORM,
        'embedlink': link,
    }
    resp = app.post('/submit/literary', form, status=303 if normalized else 422).maybe_follow()

    if normalized:
        assert resp.html.select_one('iframe.gdoc')['src'] == normalized
    else:
        assert resp.html.find(id='error_content').p.decode_contents() == 'The link you provided isn’t a valid Google Docs embed link. If you’re not sure which link to use, we have <a href="/help/google-drive-embed">a guide on publishing documents from Google Docs</a> that might help.'


@pytest.mark.usefixtures('db')
def test_google_docs_embed_edit(app, submission_user):
    make_link = 'https://docs.google.com/document/d/e/2PACX-1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli6BkxBD9QG9QmjO68C17nx_wcEOq4uC2AdVcGGr{}5/pub?embedded=true'.format

    app.set_cookie(*db_utils.create_session(submission_user).split("=", 1))

    form = {
        **BASE_LITERARY_FORM,
        'embedlink': make_link(1),
    }
    resp = app.post('/submit/literary', form, status=303).maybe_follow()
    resp = resp.click('Edit Submission Details')
    form = resp.forms['editsubmission']

    form['embedlink'] = 'https://docs.google.com/document/d/1Hheu7cs9fxBIMdFSNozPOKsXS79QEoUNhx2AFli/edit?usp=sharing'
    form.submit(status=422)

    form['embedlink'] = 'javascript:alert(1)//' + make_link(2)
    resp = form.submit(status=303).maybe_follow()
    assert resp.html.select_one('iframe.gdoc')['src'] == make_link(2)

    form['embedlink'] = make_link(3)
    resp = form.submit(status=303).maybe_follow()
    assert resp.html.select_one('iframe.gdoc')['src'] == make_link(3)


class CrosspostHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        self.end_headers()
        self.wfile.write(read_asset('img/wesley1.png'))

    def log_message(self, format, *args):
        pass


@pytest.mark.usefixtures('db')
def test_crosspost(app, submission_user, monkeypatch):
    monkeypatch.setattr(submission, '_ALLOWED_CROSSPOST_HOST', re.compile(r'\Alocalhost:[0-9]+\Z'))

    with HTTPServer(('127.0.0.1', 0), CrosspostHandler) as crosspost_test_server:
        image_url = 'http://localhost:%i/wesley1.png' % (crosspost_test_server.server_port,)

        test_server_thread = threading.Thread(
            target=crosspost_test_server.serve_forever,
            kwargs={'poll_interval': 0.1},
        )
        test_server_thread.start()

        # Crossposting from a supported source works
        try:
            v1 = create_visual(app, submission_user, imageURL=image_url)
        finally:
            crosspost_test_server.shutdown()
            test_server_thread.join()

    v1_image_url = app.get('/~submissiontest/submissions/%i/test-title' % (v1,)).html.find(id='detail-art').img['src']

    with open(get_storage_path(v1_image_url), 'rb') as f:
        assert f.read() == read_asset('img/wesley1.png')

    # Crossposting from an unsupported source doesn’t work
    form = dict(
        BASE_VISUAL_FORM,
        imageURL='http://test.invalid/wesley1.png',
    )
    cookie = db_utils.create_session(submission_user)
    resp = app.post('/submit/visual', form, headers={'Cookie': cookie}, status=422)
    assert resp.html.find(id='error_content').p.text == 'The image you crossposted was from an unsupported source. Please report this bug to the creator of the crossposting tool.'


@pytest.mark.usefixtures('db', 'cache')
def test_folder_navigation_sfw_mode(app, submission_user):
    """
    Test that a user’s own submissions are still hidden in SFW mode when rated above their configured SFW mode rating.
    """
    app.set_cookie(*db_utils.create_session(submission_user).split("=", 1))

    s1 = db_utils.create_submission(submission_user, rating=ratings.GENERAL.code)
    s2 = db_utils.create_submission(submission_user, rating=ratings.MATURE.code)
    s3 = db_utils.create_submission(submission_user, rating=ratings.GENERAL.code)

    assert app.get(f"/~submissiontest/submissions/{s1}/test-title").html.find(id='folder-nav-next')['href'] == f"/~submissiontest/submissions/{s2}/test-title"
    app.set_cookie('sfwmode', 'sfw')
    assert app.get(f"/~submissiontest/submissions/{s1}/test-title").html.find(id='folder-nav-next')['href'] == f"/~submissiontest/submissions/{s3}/test-title"


@pytest.mark.usefixtures('db', 'cache')
def test_reject_and_undo_suggested_tag(app, submission_user):
    submitter_cookie = db_utils.create_session(submission_user)
    submission = create_visual(
        app, submission_user,
        submitfile=webtest.Upload('wesley1.png', read_asset('img/wesley1.png'), 'image/png'),
    )

    tagger_user = db_utils.create_user('tagger_user')
    tagger_cookie = db_utils.create_session(tagger_user)

    submit_tag_form = {
        'submitid': submission,
        'tags': 'otter',
    }

    app.post('/submit/tags', submit_tag_form, headers={'Cookie': tagger_cookie})

    assert app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': tagger_cookie}).html.find(class_='tag-suggested', string='otter')
    assert app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': submitter_cookie}).html.find(class_='tag-suggested', string='otter')

    resp = app.put(f'/api-unstable/tag-suggestions/submit/{submission}/otter/status', 'reject', headers={'Cookie': submitter_cookie})
    assert resp.body.startswith(b'\x01')
    undo_token = resp.body[1:]

    app.put(f'/api-unstable/tag-suggestions/submit/{submission}/otter/feedback', {'reason': 'incorrect'}, headers={'Cookie': submitter_cookie})

    assert not app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': tagger_cookie}).html.find(class_='tag-suggested', string='otter')
    assert not app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': submitter_cookie}).html.find(class_='tag-suggested', string='otter')

    app.delete(f'/api-unstable/tag-suggestions/submit/{submission}/otter/status', undo_token, headers={'Cookie': submitter_cookie})

    assert app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': tagger_cookie}).html.find(class_='tag-suggested', string='otter')
    assert app.get(f'/~submissiontest/submissions/{submission}/test-title', headers={'Cookie': submitter_cookie}).html.find(class_='tag-suggested', string='otter')

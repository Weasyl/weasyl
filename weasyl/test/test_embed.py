import json
import weasyl.define as d
from weasyl.embed import BlueskyAtUriExtractor, get_embed

import pytest
from requests import Response


def _mock_response(*, with_thumbnail: bool):
    response = Response()

    if _mock_response.call_count == 0:
        obj = {
            'html': '<blockquote data-bluesky-uri="at://did:plc:test/app.bsky.feed.post/test"></blockquote>',
        }
    elif _mock_response.call_count == 1:
        obj = {
            'posts': [
                {
                    'embed': {
                        'playlist': 'https://test.invalid/playlist',
                    },
                },
            ],
        }

        if with_thumbnail:
            obj['posts'][0]['embed']['thumbnail'] = 'https://test.invalid/thumbnail'
    else:
        pytest.fail('called mocked weasyl.define.http_get too many times')

    response._content = json.dumps(obj).encode()
    _mock_response.call_count += 1
    return response


def test_bluesky_at_uri_extractor():
    html = '''
        <blockquote class="bluesky-embed" data-bluesky-uri="at://did:plc:test/app.bsky.feed.post/test" data-bluesky-cid="test">
            <p lang="en">Test</p>&mdash;
            <a href="https://bsky.app/profile/did:plc:test?ref_src=embed">Test (@test)</a>
            <a href="https://bsky.app/profile/did:plc:test/post/test?ref_src=embed">2025-01-24T20:59:37.934Z</a>
        </blockquote>
        <script async src="https://embed.bsky.app/static/embed.js" charset="utf-8"></script>
    '''

    extractor = BlueskyAtUriExtractor()
    extractor.feed(html)

    assert extractor.at_uri == 'at://did:plc:test/app.bsky.feed.post/test'


def test_bluesky_at_uri_extractor_unexpected_input():
    extractor = BlueskyAtUriExtractor()
    extractor.feed('ferrets <p>weasels</p> <blockquote>foo</blockquote>')

    assert extractor.at_uri is None


def test_get_embed_bluesky_oembed_fallback_no_at_uri(monkeypatch, cache):
    response = Response()
    response._content = json.dumps({'html': 'bad oEmbed response here'}).encode()

    with monkeypatch.context() as patch:
        patch.setattr(d, 'http_get', lambda _: response)
        embed = get_embed('https://example.bsky.app')

    assert embed['html'] == 'bad oEmbed response here'
    assert embed['needs_hls'] is False
    assert 'thumbnail_url' not in embed


def test_get_embed_bluesky_oembed_fallback_bad_post_api_response(monkeypatch, cache):
    response = Response()
    html = '<blockquote data-bluesky-uri="at://did:plc:test/app.bsky.feed.post/test"></blockquote>'
    # Use the mocked oEmbed response for the mocked Bluesky post API call too,
    # simulating the case where the response from Bluesky oEmbed API is
    # well-formed but the subsequent post API call is not.
    response._content = json.dumps({'html': html}).encode()

    with monkeypatch.context() as patch:
        patch.setattr(d, 'http_get', lambda _: response)
        embed = get_embed('https://example.bsky.app')

    assert embed['html'] == html
    assert embed['needs_hls'] is False
    assert 'thumbnail_url' not in embed


def test_get_embed_bluesky_video_with_thumbnail(monkeypatch, cache):
    _mock_response.call_count = 0

    with monkeypatch.context() as patch:
        patch.setattr(d, 'http_get', lambda _: _mock_response(with_thumbnail=True))
        embed = get_embed('https://example.bsky.app')

    assert embed['html'] == '<video id="hls-video" src="https://test.invalid/playlist" controls></video>'
    assert embed['needs_hls'] is True
    assert embed['thumbnail_url'] == 'https://test.invalid/thumbnail'


def test_get_embed_bluesky_video_without_thumbnail(monkeypatch, cache):
    _mock_response.call_count = 0

    with monkeypatch.context() as patch:
        patch.setattr(d, 'http_get', lambda _: _mock_response(with_thumbnail=False))
        embed = get_embed('https://example.bsky.app')

    assert embed['html'] == '<video id="hls-video" src="https://test.invalid/playlist" controls></video>'
    assert embed['needs_hls'] is True
    assert 'thumbnail_url' not in embed

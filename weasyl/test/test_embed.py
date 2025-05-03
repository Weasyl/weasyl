from weasyl.embed import BlueskyAtUriExtractor


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

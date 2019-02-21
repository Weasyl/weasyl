# encoding: utf-8
from __future__ import absolute_import

import pytest

from libweasyl.text import markdown, markdown_excerpt, markdown_link


user_linking_markdown_tests = [
    ('<~spam>', '<a href="/~spam">spam</a>'),
    ('<!spam>', '<a class="user-icon" href="/~spam"><img alt="spam" src="/~spam/avatar"></a>'),
    ('![](user:spam)![](user:spam)',
     '<a class="user-icon" href="/~spam"><img alt="spam" src="/~spam/avatar"></a>'
     '<a class="user-icon" href="/~spam"><img alt="spam" src="/~spam/avatar"></a>'),
    ('<!~spam>', '<a class="user-icon" href="/~spam"><img alt="" src="/~spam/avatar"> <span>spam</span></a>'),
    ('<user:spam>', '<a href="/~spam">spam</a>'),
    ('<fa:spam>', '<a href="https://www.furaffinity.net/user/spam" rel="nofollow">spam</a>'),
    ('<da:spam>', '<a href="https://spam.deviantart.com/" rel="nofollow">spam</a>'),
    ('<ib:spam>', '<a href="https://inkbunny.net/spam" rel="nofollow">spam</a>'),
    ('<sf:spam>', '<a href="https://spam.sofurry.com/" rel="nofollow">spam</a>'),
]


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_basic_user_linking(target, expected):
    assert markdown(target) == '<p>%s</p>' % (expected,)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_tag(target, expected):
    assert markdown('<em>%s</em>' % (target,)) == '<p><em>%s</em></p>' % (expected,)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_tail(target, expected):
    assert markdown('<em>eggs</em>%s' % (target,)) == '<p><em>eggs</em>%s</p>' % (expected,)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag(target, expected):
    assert markdown('<em>%s %s</em>' % (target, target)) == '<p><em>%s %s</em></p>' % (expected, expected)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag_with_more_text_between(target, expected):
    assert markdown('<em>%s spam %s</em>' % (target, target)) == '<p><em>%s spam %s</em></p>' % (expected, expected)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tail(target, expected):
    assert markdown('<em>eggs</em>%s %s' % (target, target)) == (
        '<p><em>eggs</em>%s %s</p>' % (expected, expected))


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tail_with_more_text_betweeen(target, expected):
    assert markdown('<em>eggs</em>%s spam %s' % (target, target)) == (
        '<p><em>eggs</em>%s spam %s</p>' % (expected, expected))


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_markdown(target, expected):
    assert markdown('*%s*' % (target,)) == '<p><em>%s</em></p>' % (expected,)


def test_markdown_no_user_links_in_code():
    assert markdown('<code><~spam></code>') == '<p><code>&lt;~spam&gt;</code></p>'


def test_markdown_no_user_links_in_pre():
    assert markdown('<pre><~spam></pre>') == '<pre><p>&lt;~spam&gt;</p></pre>'


def test_markdown_no_user_links_in_links():
    assert markdown('<a><~spam></a>') == '<p><a>&lt;~spam&gt;</a></p>'


def test_markdown_multi_element():
    assert markdown('one\n\ntwo') == '<p>one</p>\n\n<p>two</p>'


def test_markdown_user_linking_with_underscore():
    assert markdown('<~hello_world>') == '<p><a href="/~helloworld">hello_world</a></p>'


def test_markdown_image_replacement():
    assert markdown('![example](http://example)') == '<p><a href="http://example" rel="nofollow">example</a></p>'


def test_forum_whitelist():
    assert markdown('https://forums.weasyl.com/foo') == (
        '<p><a href="https://forums.weasyl.com/foo">https://forums.weasyl.com/foo</a></p>')


def test_markdown_unordered_list():
    assert markdown('- five\n- six\n- seven') == '<ul><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ul>'


def test_markdown_regular_ordered_list_start():
    assert markdown('1. five\n1. six\n1. seven') == '<ol start="1"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_respect_ordered_list_start():
    assert markdown('5. five\n6. six\n7. seven') == '<ol start="5"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_strikethrough():
    assert markdown(u"~~test~~") == u"<p><del>test</del></p>"


def test_markdown_class():
    assert markdown(u'<div class="align-center">center</div>') == u'<div class="align-center"><p>center</p></div>'
    assert markdown(u'<div class="align-other">other</div>') == u'<div><p>other</p></div>'


@pytest.mark.parametrize(('target', 'expected'), [
    (u'<span style="margin: 1em">margin</span>', u'<span style="">margin</span>'),
    (u'<span style="color: #f00">red</span>', u'<span style="color: #f00">red</span>'),
])
def test_markdown_style(target, expected):
    assert markdown(target) == u"<p>%s</p>" % (expected,)


@pytest.mark.parametrize(('target', 'expected'), [
    (u"[external](http://example.com/)", u'<a href="http://example.com/" rel="nofollow">external</a>'),
    (u'<a href="http://example.com/">external</a>', u'<a href="http://example.com/" rel="nofollow">external</a>'),
    (u'<a href="http://example.com/" rel="noreferrer">external</a>', u'<a href="http://example.com/" rel="nofollow">external</a>'),
    (u"[external](//example.com/)", u'<a href="//example.com/" rel="nofollow">external</a>'),
])
def test_markdown_external_link_noreferrer(target, expected):
    assert markdown(target) == u"<p>%s</p>" % (expected,)


markdown_link_tests = [
    (('spam', '/eggs'), '[spam](/eggs)'),
    ((']spam[', '/eggs'), r'[\]spam\[](/eggs)'),
    (('[[spam]', '/eggs'), r'[\[\[spam\]](/eggs)'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_link_tests)
def test_markdown_link(target, expected):
    assert markdown_link(*target) == expected


def test_tag_stripping():
    assert markdown(u"<button>text</button>") == u"<p>&lt;button&gt;text&lt;/button&gt;</p>"
    assert markdown(u"<button><button>text</button></button>") == u"<p>&lt;button&gt;&lt;/button&gt;&lt;button&gt;text&lt;/button&gt;</p>"
    assert markdown(u"<!--[if IE]><script>alert(1)</script><![endif]-->") == u""


def test_link_stripping():
    assert markdown(u"[link](data:text/html,foo)") == u"<p><a>link</a></p>"


markdown_excerpt_tests = [
    (u'', u''),
    (u'short', u'short'),
    (u'just short enoughAAAAAAAAAAAAA', u'just short enoughAAAAAAAAAAAAA'),
    (u'not short enoughAAAAAAAAAAAAAAA', u'not short enoughAAAAAAAAAAAAA…'),
    (u'*leading* inline formatting', u'leading inline formatting'),
    (u'middle *inline* formatting', u'middle inline formatting'),
    (u'trailing inline *formatting*', u'trailing inline formatting'),
    (u'*nested **inline** formatting*', u'nested inline formatting'),
    (u'   unnecessary  whitespace\t', u'unnecessary whitespace'),
    (u'multiple\nlines', u'multiple lines'),
    (u'multiple  \nlines', u'multiple lines'),
    (u'multiple\n\nparagraphs', u'multiple paragraphs'),
    (u'Üñíçôđe\N{COMBINING ACUTE ACCENT}', u'Üñíçôđe\N{COMBINING ACUTE ACCENT}'),
    (u'single-codepoint graphemes😊😊😊😊', u'single-codepoint graphemes😊😊😊😊'),
    (u'single-codepoint graphemes😊😊😊😊😊', u'single-codepoint graphemes😊😊😊…'),
    (u'test\n - lists\n - of\n - items\n\ntest', u'test lists of items test'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_excerpt_tests)
def test_excerpt(target, expected):
    assert markdown_excerpt(target, length=30) == expected


def test_excerpt_default_length():
    assert markdown_excerpt(u'a' * 300) == u'a' * 300
    assert markdown_excerpt(u'a' * 301) == u'a' * 299 + u'…'

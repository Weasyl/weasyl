# encoding: utf-8
from __future__ import absolute_import

from lxml.etree import LIBXML_VERSION
import pytest

from libweasyl.text import markdown, markdown_excerpt, markdown_link


libxml_xfail = pytest.mark.xfail(LIBXML_VERSION < (2, 9), reason='libxml2 too old to preserve whitespace')

user_linking_markdown_tests = [
    ('<~spam>', '<a href="/~spam">spam</a>'),
    ('<!spam>', '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'),
    ('![](user:spam)![](user:spam)',
     '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'
     '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'),
    ('<!~spam>', '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"> <span>spam</span></a>'),
    ('![user image with alt text](user:example)', '<a href="/~example" class="user-icon"><img src="/~example/avatar"> <span>user image with alt text</span></a>'),
    ('<user:spam>', '<a href="/~spam">spam</a>'),
    ('[link](user:spam)', '<a href="/~spam">link</a>'),
    ('<fa:spam>', '<a href="https://www.furaffinity.net/user/spam" rel="nofollow ugc">spam</a>'),
    ('<da:spam>', '<a href="https://www.deviantart.com/spam" rel="nofollow ugc">spam</a>'),
    ('<ib:spam>', '<a href="https://inkbunny.net/spam" rel="nofollow ugc">spam</a>'),
    ('<sf:spam>', '<a href="https://spam.sofurry.com/" rel="nofollow ugc">spam</a>'),
]


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_basic_user_linking(target, expected):
    assert markdown(target) == '<p>%s</p>\n' % (expected,)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_tag(target, expected):
    assert markdown('<em>%s</em>' % (target,)) == '<p><em>%s</em></p>\n' % (expected,)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_tail(target, expected):
    assert markdown('<em>eggs</em>%s' % (target,)) == '<p><em>eggs</em>%s</p>\n' % (expected,)


@libxml_xfail
@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag(target, expected):
    assert markdown('<em>%s %s</em>' % (target, target)) == '<p><em>%s %s</em></p>\n' % (expected, expected)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag_with_more_text_between(target, expected):
    assert markdown('<em>%s spam %s</em>' % (target, target)) == '<p><em>%s spam %s</em></p>\n' % (expected, expected)


@libxml_xfail
@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tail(target, expected):
    assert markdown('<em>eggs</em>%s %s' % (target, target)) == (
        '<p><em>eggs</em>%s %s</p>\n' % (expected, expected))


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tail_with_more_text_betweeen(target, expected):
    assert markdown('<em>eggs</em>%s spam %s' % (target, target)) == (
        '<p><em>eggs</em>%s spam %s</p>\n' % (expected, expected))


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_in_markdown(target, expected):
    assert markdown('*%s*' % (target,)) == '<p><em>%s</em></p>\n' % (expected,)


def test_markdown_no_user_links_in_code():
    assert markdown('<code><~spam></code>') == '<p><code>&lt;~spam&gt;</code></p>\n'


def test_markdown_no_user_links_in_pre():
    assert markdown('<pre><~spam></pre>') == '<pre><p>&lt;~spam&gt;</p></pre>\n'


def test_markdown_no_user_links_in_links():
    assert markdown('<a><~spam></a>') == '<p><a>&lt;~spam&gt;</a></p>\n'


def test_markdown_escaped_user_link():
    assert markdown('\\\\<~spam>') == '<p>&lt;~spam&gt;</p>\n'


def test_markdown_multi_element():
    assert markdown('one\n\ntwo') == '<p>one</p>\n\n<p>two</p>\n'


def test_markdown_user_linking_with_underscore():
    assert markdown('<~hello_world>') == '<p><a href="/~helloworld">hello_world</a></p>\n'


def test_markdown_image_replacement():
    assert markdown('![example](http://example)') == '<p><a href="http://example" rel="nofollow ugc">example</a></p>\n'
    assert markdown('<img alt="broken">') == '<p><a href="">broken</a></p>\n'


def test_forum_whitelist():
    assert markdown('https://forums.weasyl.com/foo') == (
        '<p><a href="https://forums.weasyl.com/foo">https://forums.weasyl.com/foo</a></p>\n')


def test_markdown_unordered_list():
    assert markdown('- five\n- six\n- seven') == '<ul><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ul>'


def test_markdown_regular_ordered_list_start():
    assert markdown('1. five\n1. six\n1. seven') == '<ol start="1"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_respect_ordered_list_start():
    assert markdown('5. five\n6. six\n7. seven') == '<ol start="5"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_strikethrough():
    assert markdown(u"~~test~~") == u"<p><del>test</del></p>\n"


@pytest.mark.parametrize(('target', 'expected'), [
    (u"[external](http://example.com/)", u'<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    (u'<a href="http://example.com/">external</a>', u'<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    (u'<a href="http://example.com/" rel="noreferrer">external</a>', u'<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    (u"[external](//example.com/)", u'<a href="//example.com/" rel="nofollow ugc">external</a>'),
])
def test_markdown_external_link_noreferrer(target, expected):
    assert markdown(target) == u"<p>%s</p>\n" % (expected,)


markdown_link_tests = [
    (('spam', '/eggs'), '[spam](/eggs)'),
    ((']spam[', '/eggs'), r'[\]spam\[](/eggs)'),
    (('[[spam]', '/eggs'), r'[\[\[spam\]](/eggs)'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_link_tests)
def test_markdown_link(target, expected):
    assert markdown_link(*target) == expected


def test_tag_stripping():
    assert markdown(u"<button>text</button>") == u"<p>text</p>\n"
    assert markdown(u"<button><button>text</button></button>") == u"<p>text</p>\n"
    assert markdown(u"<!--[if IE]><script>alert(1)</script><![endif]-->") == u"\n"


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

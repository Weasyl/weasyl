# encoding: utf-8


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


@libxml_xfail
@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag(target, expected):
    assert markdown('<em>%s %s</em>' % (target, target)) == '<p><em>%s %s</em></p>' % (expected, expected)


@pytest.mark.parametrize(('target', 'expected'), user_linking_markdown_tests)
def test_markdown_user_linking_twice_in_tag_with_more_text_between(target, expected):
    assert markdown('<em>%s spam %s</em>' % (target, target)) == '<p><em>%s spam %s</em></p>' % (expected, expected)


@libxml_xfail
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


def test_markdown_escaped_user_link():
    assert markdown('\\\\<~spam>') == '<p>&lt;~spam&gt;</p>'


def test_markdown_multi_element():
    assert markdown('one\n\ntwo') == '<p>one</p><p>two</p>'


def test_markdown_user_linking_with_underscore():
    assert markdown('<~hello_world>') == '<p><a href="/~helloworld">hello_world</a></p>'


def test_markdown_image_replacement():
    assert markdown('![example](http://example)') == '<p><a href="http://example" rel="nofollow">example</a></p>'


def test_forum_whitelist():
    assert markdown('https://forums.weasyl.com/foo') == (
        '<p><a href="https://forums.weasyl.com/foo">https://forums.weasyl.com/foo</a></p>')


def test_markdown_unordered_list():
    assert markdown('- five\n- six\n- seven') == '<ul><li>five</li><li>six</li><li>seven</li></ul>'


def test_markdown_regular_ordered_list_start():
    assert markdown('1. five\n1. six\n1. seven') == '<ol start="1"><li>five</li><li>six</li><li>seven</li></ol>'


def test_markdown_respect_ordered_list_start():
    assert markdown('5. five\n6. six\n7. seven') == '<ol start="5"><li>five</li><li>six</li><li>seven</li></ol>'


def test_markdown_strikethrough():
    assert markdown("~~test~~") == "<p><del>test</del></p>"


@pytest.mark.parametrize(('target', 'expected'), [
    ("[external](http://example.com/)", '<a href="http://example.com/" rel="nofollow">external</a>'),
    ('<a href="http://example.com/">external</a>', '<a href="http://example.com/" rel="nofollow">external</a>'),
    ('<a href="http://example.com/" rel="noreferrer">external</a>', '<a href="http://example.com/" rel="nofollow">external</a>'),
    ("[external](//example.com/)", '<a href="//example.com/" rel="nofollow">external</a>'),
])
def test_markdown_external_link_noreferrer(target, expected):
    assert markdown(target) == "<p>%s</p>" % (expected,)


markdown_link_tests = [
    (('spam', '/eggs'), '[spam](/eggs)'),
    ((']spam[', '/eggs'), r'[\]spam\[](/eggs)'),
    (('[[spam]', '/eggs'), r'[\[\[spam\]](/eggs)'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_link_tests)
def test_markdown_link(target, expected):
    assert markdown_link(*target) == expected


def test_tag_stripping():
    assert markdown("<button>text</button>") == "<p>text</p>"
    assert markdown("<button><button>text</button></button>") == "<p>text</p>"
    assert markdown("<!--[if IE]><script>alert(1)</script><![endif]-->") == ""


markdown_excerpt_tests = [
    ('', ''),
    ('short', 'short'),
    ('just short enoughAAAAAAAAAAAAA', 'just short enoughAAAAAAAAAAAAA'),
    ('not short enoughAAAAAAAAAAAAAAA', 'not short enoughAAAAAAAAAAAAA…'),
    ('*leading* inline formatting', 'leading inline formatting'),
    ('middle *inline* formatting', 'middle inline formatting'),
    ('trailing inline *formatting*', 'trailing inline formatting'),
    ('*nested **inline** formatting*', 'nested inline formatting'),
    ('   unnecessary  whitespace\t', 'unnecessary whitespace'),
    ('multiple\nlines', 'multiple lines'),
    ('multiple  \nlines', 'multiple lines'),
    ('multiple\n\nparagraphs', 'multiple paragraphs'),
    ('Üñíçôđe\N{COMBINING ACUTE ACCENT}', 'Üñíçôđe\N{COMBINING ACUTE ACCENT}'),
    ('single-codepoint graphemes😊😊😊😊', 'single-codepoint graphemes😊😊😊😊'),
    ('single-codepoint graphemes😊😊😊😊😊', 'single-codepoint graphemes😊😊😊…'),
    ('test\n - lists\n - of\n - items\n\ntest', 'test lists of items test'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_excerpt_tests)
def test_excerpt(target, expected):
    assert markdown_excerpt(target, length=30) == expected


def test_excerpt_default_length():
    assert markdown_excerpt('a' * 300) == 'a' * 300
    assert markdown_excerpt('a' * 301) == 'a' * 299 + '…'

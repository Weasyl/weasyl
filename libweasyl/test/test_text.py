# encoding: utf-8
from lxml import html
from lxml.etree import LIBXML_VERSION
import pytest

from libweasyl.defang import defang
from libweasyl.text import markdown, markdown_excerpt, markdown_link, strip_outer_tag


libxml_xfail = pytest.mark.xfail(LIBXML_VERSION < (2, 9), reason='libxml2 too old to preserve whitespace')

user_linking_markdown_tests = [
    ('<~spam>', '<a href="/~spam">spam</a>'),
    ('<!spam>', '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'),
    ('![](user:spam)![](user:spam)',
     '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'
     '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt="spam"></a>'),
    ('<!~spam>', '<a href="/~spam" class="user-icon"><img src="/~spam/avatar" alt=""> <span>spam</span></a>'),
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
    assert markdown('![example](http://example/)') == '<p><a href="http://example/" rel="nofollow ugc">example</a></p>\n'
    assert markdown('<img alt="broken">') == '<p><span class="invalid-markup" title="invalid link">broken []</span></p>\n'


def test_internal_links_without_nofollow():
    assert markdown('https://www.weasyl.com/search?q=foo') == (
        '<p><a href="https://www.weasyl.com/search?q=foo">https://www.weasyl.com/search?q=foo</a></p>\n')


def test_markdown_no_autolink_in_html_link():
    assert markdown('[https://foo.test/](https://bar.test/)') == '<p><a href="https://bar.test/" rel="nofollow ugc">https://foo.test/</a></p>\n'
    assert markdown('[@foo@bar.test](https://baz.test/)') == '<p><a href="https://baz.test/" rel="nofollow ugc">@foo@bar.test</a></p>\n'
    assert markdown('<a href="https://bar.test/">https://foo.test/</a>') == '<p><a href="https://bar.test/" rel="nofollow ugc">https://foo.test/</a></p>\n'
    assert markdown('<A href="https://baz.test/">@foo@bar.test</A>') == '<p><a href="https://baz.test/" rel="nofollow ugc">@foo@bar.test</a></p>\n'
    assert markdown('<a href="https://baz.test/">@foo@bar.test</a>') == '<p><a href="https://baz.test/" rel="nofollow ugc">@foo@bar.test</a></p>\n'
    assert markdown('<b>https://foo.test/</b>') == '<p><b><a href="https://foo.test/" rel="nofollow ugc">https://foo.test/</a></b></p>\n'
    assert markdown('<b>@foo@bar.test</b>') == '<p><b>@<a href="mailto:foo@bar.test" rel="nofollow ugc">foo@bar.test</a></b></p>\n'


def test_markdown_unordered_list():
    assert markdown('- five\n- six\n- seven') == '<ul><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ul>'


def test_markdown_regular_ordered_list_start():
    assert markdown('1. five\n1. six\n1. seven') == '<ol start="1"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_respect_ordered_list_start():
    assert markdown('5. five\n6. six\n7. seven') == '<ol start="5"><li>five</li>\n<li>six</li>\n<li>seven</li>\n</ol>'


def test_markdown_strikethrough():
    assert markdown("~~test~~") == "<p><del>test</del></p>\n"


@pytest.mark.parametrize(('target', 'expected'), [
    ("[external](http://example.com/)", '<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    ('<a href="http://example.com/">external</a>', '<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    ('<a href="http://example.com/" rel="noreferrer">external</a>', '<a href="http://example.com/" rel="nofollow ugc">external</a>'),
    ("[external](//example.com/)", '<a href="https://example.com/" rel="nofollow ugc">external</a>'),
    ('<a href=" //example.com/">external</a>', '<a href="https://example.com/" rel="nofollow ugc">external</a>'),
])
def test_markdown_external_link_noreferrer(target, expected):
    assert markdown(target) == "<p>%s</p>\n" % (expected,)


markdown_link_tests = [
    (('spam', '/eggs'), '[spam](/eggs)'),
    ((']spam[', '/eggs'), r'[\]spam\[](/eggs)'),
    (('[[spam]', '/eggs'), r'[\[\[spam\]](/eggs)'),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_link_tests)
def test_markdown_link(target, expected):
    assert markdown_link(*target) == expected


def test_tag_stripping():
    assert markdown("<button>text</button>") == "<p>text</p>\n"
    assert markdown("<button><button>text</button></button>") == "<p>text</p>\n"
    assert markdown("<!--[if IE]><script>alert(1)</script><![endif]-->") == "\n"


def _invalid_link(inner: str) -> str:
    return f'<span class="invalid-markup" title="invalid link">{inner}</span>'


@pytest.mark.parametrize(('target', 'expected'), [
    ('<a href=" javascript:alert(1)">no</a>', _invalid_link("no [ javascript:alert(1)]")),
    ('<a href="java&#x09;script:alert(1)">no</a>', _invalid_link("no [java\tscript:alert(1)]")),
])
def test_unsafe_link(target, expected):
    assert markdown(target) == "<p>%s</p>\n" % (expected,)


@pytest.mark.parametrize(('target', 'expected'), [
    ('<a href="example.com">no</a>', _invalid_link("no [example.com]")),
    ('<a href="example.com">no</a>tail', _invalid_link("no [example.com]") + "tail"),
    ('<a href="http:example.com">yes</a>', '<a href="http://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="https:example.com">yes</a>', '<a href="https://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="\\\\example.com\\">yes</a>', '<a href="https://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="/\\example.com/">yes</a>', '<a href="https://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="\\/example.com/">yes</a>', '<a href="https://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="\x0b HT&#x9;tps://example.com/&#xd;&#xa;">yes</a>', '<a href="https://example.com/" rel="nofollow ugc">yes</a>'),
    ('<a href="\x0b HT tps://example.com/">no\x0b</a>', _invalid_link("no [ HT tps://example.com/]")),
    ('<a href="ht tps://example.com/">no</a>', _invalid_link("no [ht tps://example.com/]")),
    ('<a href="https://example.com/&#xd800;">?</a>', '<a href="https://example.com/" rel="nofollow ugc">?</a>'),
    ('<a href="/policy/community">yes</a>', '<a href="/policy/community">yes</a>'),
    ('<a href="//example.com:https">no</a>', _invalid_link("no [//example.com:https]")),
])
def test_link_normalization(target, expected):
    assert markdown(target) == "<p>%s</p>\n" % (expected,)


@pytest.mark.parametrize(('target', 'expected'), [
    ('<a href="java\nscript:alert(1)">no</a>', "<a>no</a>"),
])
def test_unsafe_link_direct(target, expected):
    fragment = html.fragment_fromstring(target, create_parent=True)
    defang(fragment)
    start, stripped, end = strip_outer_tag(html.tostring(fragment, encoding="unicode"))
    assert stripped == expected


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
    ('<div style="text-align: center">**foo**</div>\n<!-- comment -->', "foo"),
    ('1 < 3 > 2 "foo"', '1 < 3 > 2 "foo"'),
    ("&copy;", "©"),
    ("&#xec;", "ì"),
    ('foo <!bar> baz', "foo [bar] baz"),
    (" foo\nbar  baz\t", "foo bar baz"),
    ("<![/b]>", "<![/b]>"),
]


@pytest.mark.parametrize(('target', 'expected'), markdown_excerpt_tests)
def test_excerpt(target, expected):
    assert markdown_excerpt(target, length=30) == expected


def test_excerpt_default_length():
    assert markdown_excerpt('a' * 300) == 'a' * 300
    assert markdown_excerpt('a' * 301) == 'a' * 299 + '…'

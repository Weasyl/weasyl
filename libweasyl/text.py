# encoding: utf-8
from html import escape as html_escape
import re

from lxml import etree, html
import misaka

from weasyl.forms import parse_sysname
from .defang import CleanHref
from .defang import defang

try:
    from html.parser import locatestarttagend_tolerant as locatestarttagend
except ImportError:
    from html.parser import locatestarttagend


def slug_for(title: str) -> str:
    title = title.replace("&", " and ")
    return "-".join(m.group(0) for m in re.finditer(r"[a-z0-9]+", title.lower()))


def summarize(s, max_length=200):
    if len(s) > max_length:
        return s[:max_length - 1].rstrip() + '\N{HORIZONTAL ELLIPSIS}'
    return s


AUTOLINK_URL = (
    r"(?P<url>\b(?:https?://|www\d{,3}\.|[a-z0-9.-]+\.[a-z]{2,4}/)[^\s()"
    r"<>\[\]\x02]+(?![^\s`!()\[\]{};:'\".,<>?\x02\xab\xbb\u201c\u201d\u2018"
    r"\u2019]))"
)

url_regexp = re.compile(AUTOLINK_URL, re.I | re.S)

USER_LINK = re.compile(r"""
    \\(?P<escaped>[\\<])
| <(?P<type>!~|[!~])(?P<username>[a-z0-9_]+)>
""", re.I | re.X)

NON_USERNAME_CHARACTERS = re.compile("[^a-z0-9]+", re.I)

_EXCERPT_BLOCK_ELEMENTS = frozenset([
    "blockquote", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "ol",
    "p", "pre", "ul", "li",
])

# C0 minus [\t\n\r]
_LXML_INCOMPATIBLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _furaffinity(target):
    return "".join(i for i in target if i not in "!#_" and not i.isspace()).lower()


def _inkbunny(target):
    return target.lower()


def _deviantart(target):
    return "".join(i for i in target if i != "." and not i.isspace()).lower()


def _sofurry(target):
    return NON_USERNAME_CHARACTERS.sub("-", target).lstrip("-").lower()


MISAKA_EXT = (
    misaka.EXT_TABLES |
    misaka.EXT_FENCED_CODE |
    misaka.EXT_AUTOLINK |
    misaka.EXT_STRIKETHROUGH |
    misaka.EXT_NO_INTRA_EMPHASIS |
    misaka.EXT_LAX_SPACING |
    misaka.EXT_NO_INDENTED_CODE_BLOCKS)

MISAKA_FORMAT = (
    misaka.HTML_HARD_WRAP)


def strip_outer_tag(html):
    match = locatestarttagend.match(html)
    start_tag_end = match.end()
    end_tag_start = html.rindex('<')
    return html[:start_tag_end + 1], html[start_tag_end + 1:end_tag_start], html[end_tag_start:]


class WeasylRenderer(misaka.HtmlRenderer):
    # Render Markdown in HTML
    def block_html(self, raw_html):
        if raw_html.startswith('<!--'):
            return raw_html
        start, stripped, end = strip_outer_tag(raw_html)
        return ''.join([start, _markdown(stripped).rstrip(), end])

    def autolink(self, link, is_email):
        # default implementation from sundown’s `rndr_autolink`, with the tag name replaced
        html_href = html_escape("mailto:" + link if is_email else link)
        html_text = html_escape(link.removeprefix("mailto:"))

        return f'<wzl-autolink href="{html_href}">{html_text}</wzl-autolink>'

    # Respect start of ordered lists
    def list(self, text, ordered, prefix):
        if prefix:
            return '<ol start="{start}">{text}</ol>'.format(
                start=prefix,
                text=text,
            )
        else:
            return '<ul>{text}</ul>'.format(
                text=text,
            )


def _markdown(target):
    renderer = WeasylRenderer(MISAKA_FORMAT)
    markdown = misaka.Markdown(renderer, MISAKA_EXT)
    return markdown.render(target)


def create_link(t, username):
    sysname = parse_sysname(username)
    if sysname is None:
        e = etree.Element("span")
        e.set("class", "invalid-markup")
        e.set("title", "invalid username")
        e.text = f"<{t}{username}>"
        return e

    link = etree.Element("a")
    link.set("href", f"/~{sysname}")

    if t == "~":
        link.text = username
    else:
        link.set("class", "user-icon")

        image = etree.SubElement(link, "img")
        image.set("src", f"/~{sysname}/avatar")

        if t == "!":
            image.set("alt", username)
        else:
            image.set("alt", "")
            label = etree.SubElement(link, "span")
            label.text = username
            image.tail = " "

    return link


def add_user_links(fragment, parent, can_contain):
    def add_matches(text, got_link):
        text_start = 0

        for m in USER_LINK.finditer(text):
            match_start = m.start()

            if match_start > text_start:
                previous_text.append(text[text_start:match_start])

            text_start = m.end()

            escaped, t, username = m.group("escaped", "type", "username")

            if escaped:
                previous_text.append(escaped)
            else:
                got_link(t, username)

        if text_start == 0:
            return False

        if text_start < len(text):
            previous_text.append(text[text_start:])

        return True

    def got_text_link(t, username):
        nonlocal previous
        nonlocal insert_index

        if previous is None:
            fragment.text = "".join(previous_text)
        else:
            previous.tail = "".join(previous_text)

        del previous_text[:]

        link = create_link(t, username)
        fragment.insert(insert_index, link)
        insert_index += 1

        previous = link

    def got_tail_link(t, username):
        nonlocal previous
        nonlocal insert_index

        previous.tail = "".join(previous_text)
        del previous_text[:]

        insert_index += 1
        link = create_link(t, username)
        parent.insert(insert_index, link)

        previous = link

    if can_contain:
        for child in list(fragment):
            child_can_contain = child.tag not in ("a", "pre", "code")
            add_user_links(child, fragment, child_can_contain)

        if fragment.text:
            previous = None
            insert_index = 0
            previous_text = []

            if add_matches(fragment.text, got_text_link):
                if previous is None:
                    fragment.text = "".join(previous_text)
                else:
                    previous.tail = "".join(previous_text)

    if fragment.tail:
        previous = fragment
        insert_index = parent.index(fragment)
        previous_text = []

        if add_matches(fragment.tail, got_tail_link):
            previous.tail = "".join(previous_text)


def _convert_autolinks(fragment):
    for child in fragment:
        if child.tag in ("a", "wzl-autolink"):
            child.tag = "a"
            link = child
            href = link.get("href")

            if href:
                t, _, user = href.partition(":")

                if t == "user" and (sysname := parse_sysname(user)) is not None:
                    link.set("href", f"/~{sysname}")
                elif t == "da":
                    link.set("href", "https://www.deviantart.com/{user}".format(user=_deviantart(user)))
                elif t == "ib":
                    link.set("href", "https://inkbunny.net/{user}".format(user=_inkbunny(user)))
                elif t == "fa":
                    link.set("href", "https://www.furaffinity.net/user/{user}".format(user=_furaffinity(user)))
                elif t == "sf":
                    link.set("href", "https://{user}.sofurry.com/".format(user=_sofurry(user)))
                else:
                    continue

                if not link.text or link.text == href:
                    link.text = user
        else:
            _convert_autolinks(child)


def _replace_bad_links(fragment) -> None:
    """
    Expands unsupported links to `.invalid-markup` elements to provide a better user experience than `libweasyl.defang`'s simple removal.
    """
    for link in list(fragment.iter("a")):
        href = link.get("href")
        if href is not None and CleanHref.try_from(href) is None:
            e = etree.Element("span")
            e.tail = link.tail
            e.set("class", "invalid-markup")
            e.set("title", "invalid link")
            e.text = f"{link.text} [{_LXML_INCOMPATIBLE.sub('', href)}]"
            link.getparent().replace(link, e)


def _markdown_fragment(target):
    rendered = _markdown(target)
    fragment = html.fragment_fromstring(rendered, create_parent=True)

    _convert_autolinks(fragment)

    for image in list(fragment.iter("img")):
        src = image.get("src", "")

        t, _, user = src.partition(":")

        if t != "user" or (sysname := parse_sysname(user)) is None:
            link = etree.Element("a")
            link.tail = image.tail
            link.set("href", src)
            link.text = image.get("alt", src)
            image.getparent().replace(image, link)
            continue

        image.set("src", f"/~{sysname}/avatar")

        link = etree.Element("a")
        link.set("href", f"/~{sysname}")
        link.set("class", "user-icon")
        link.tail = image.tail
        image.getparent().replace(image, link)
        link.append(image)

        alt = image.get("alt")
        if alt:
            image.tail = " "
            label = etree.SubElement(link, "span")
            label.text = alt
            del image.attrib["alt"]
        else:
            image.tail = None
            image.set("alt", user)

    _replace_bad_links(fragment)

    add_user_links(fragment, None, True)

    defang(fragment)

    return fragment


def markdown(target):
    fragment = _markdown_fragment(target)
    start, stripped, end = strip_outer_tag(html.tostring(fragment, encoding="unicode"))
    return stripped


def _itertext_spaced(element):
    if element.text:
        yield element.text
    elif element.tag == "img" and (alt := element.get("alt")):
        yield "[%s]" % (alt,)

    for child in element:
        is_block = child.tag in _EXCERPT_BLOCK_ELEMENTS

        if is_block:
            yield " "

        for t in _itertext_spaced(child):
            yield t

        if child.tail:
            yield child.tail

        if is_block:
            yield " "


def _normalize_whitespace(text):
    return re.sub(r"\s+", " ", text.strip())


def markdown_excerpt(markdown_text, length=300):
    fragment = _markdown_fragment(markdown_text)
    text = _normalize_whitespace("".join(_itertext_spaced(fragment)))

    # TODO: more generic footer removal
    text = text.removesuffix("Posted using PostyBirb").rstrip()

    if len(text) <= length:
        return text
    else:
        return text[:length - 1].rstrip() + "…"


def markdown_link(title, url):
    title = title.replace('[', '\\[').replace(']', '\\]')
    return '[%s](%s)' % (title, url)

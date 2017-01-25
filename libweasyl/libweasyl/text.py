# encoding: utf-8
from __future__ import unicode_literals

import re

from lxml import etree, html
import misaka

from .compat import unicode
from .defang import defang
from .legacy import login_name

try:
    from html.parser import locatestarttagend
except ImportError:
    try:
        from html.parser import locatestarttagend_tolerant as locatestarttagend
    except ImportError:
        from HTMLParser import locatestarttagend


def slug_for(title):
    title = title.replace("&", " and ")
    return "-".join(m.group(0) for m in re.finditer(r"[a-z0-9]+", title.lower()))


AUTOLINK_URL = (
    r"(?P<url>(?isu)\b(?:https?://|www\d{,3}\.|[a-z0-9.-]+\.[a-z]{2,4}/)[^\s()"
    r"<>\[\]\x02]+(?![^\s`!()\[\]{};:'\".,<>?\x02\xab\xbb\u201c\u201d\u2018"
    r"\u2019]))"
)

url_regexp = re.compile(AUTOLINK_URL)

USER_LINK = re.compile(r"""
    \\(?P<escaped>[\\<])
| <(?P<type>!~|[!~])(?P<username>[a-z0-9_]+)>
| .
""", re.I | re.X)

NON_USERNAME_CHARACTERS = re.compile("[^a-z0-9]+", re.I)

_EXCERPT_BLOCK_ELEMENTS = frozenset([
    "blockquote", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "ol",
    "p", "pre", "ul", "li",
])


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
    end_tag_start = html.rindex(u'<')
    return html[:start_tag_end + 1], html[start_tag_end + 1:end_tag_start], html[end_tag_start:]


class WeasylRenderer(misaka.HtmlRenderer):
    # Render Markdown in HTML
    def block_html(self, raw_html):
        if raw_html.startswith('<!--'):
            return raw_html
        start, stripped, end = strip_outer_tag(raw_html)
        return u''.join([start, _markdown(stripped).rstrip(), end])

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
    link = etree.Element(u"a")
    link.set(u"href", u"/~" + login_name(username))

    if t == "~":
        link.text = username
    else:
        link.set(u"class", u"user-icon")

        image = etree.SubElement(link, u"img")
        image.set(u"src", u"/~{username}/avatar".format(username=login_name(username)))
        image.set(u"alt", username)

        if t != "!":
            label = etree.SubElement(link, u"span")
            label.text = username
            image.tail = u" "

    return link


def add_user_links(fragment, parent, can_contain):
    _nonlocal = {}

    def add_matches(text, got_link):
        for m in USER_LINK.finditer(text):
            escaped, t, username = m.group("escaped", "type", "username")

            if escaped:
                previous_text.append(escaped)
                continue

            if not t:
                previous_text.append(m.group())
                continue

            got_link(t, username)

    def got_text_link(t, username):
        previous = _nonlocal["previous"]

        if previous is None:
            fragment.text = "".join(previous_text)
        else:
            previous.tail = "".join(previous_text)

        del previous_text[:]

        link = create_link(t, username)
        fragment.insert(_nonlocal["insert_index"], link)
        _nonlocal["insert_index"] += 1

        _nonlocal["previous"] = link

    def got_tail_link(t, username):
        _nonlocal["previous"].tail = "".join(previous_text)
        del previous_text[:]

        _nonlocal["insert_index"] += 1
        link = create_link(t, username)
        parent.insert(_nonlocal["insert_index"], link)

        _nonlocal["previous"] = link

    if can_contain:
        for child in list(fragment):
            child_can_contain = child.tag not in ("a", "pre", "code")
            add_user_links(child, fragment, child_can_contain)

        if fragment.text:
            _nonlocal["previous"] = None
            _nonlocal["insert_index"] = 0
            previous_text = []
            add_matches(fragment.text, got_text_link)

            previous = _nonlocal["previous"]

            if previous is None:
                fragment.text = "".join(previous_text)
            else:
                previous.tail = "".join(previous_text)

    if fragment.tail:
        _nonlocal["previous"] = fragment
        _nonlocal["insert_index"] = list(parent).index(fragment)
        previous_text = []
        add_matches(fragment.tail, got_tail_link)
        _nonlocal["previous"].tail = "".join(previous_text)


def _markdown_fragment(target, image):
    if not image:
        images_left = 0
    elif type(image) is int:
        images_left = image
    else:
        images_left = 5

    rendered = _markdown(target)
    fragment = html.fragment_fromstring(rendered, create_parent=True)

    for link in fragment.findall(".//a"):
        href = link.attrib.get("href")

        if href:
            t, _, user = href.partition(":")

            if t == "user":
                link.attrib["href"] = u"/~{user}".format(user=login_name(user))
            elif t == "da":
                link.attrib["href"] = u"https://{user}.deviantart.com/".format(user=_deviantart(user))
            elif t == "ib":
                link.attrib["href"] = u"https://inkbunny.net/{user}".format(user=_inkbunny(user))
            elif t == "fa":
                link.attrib["href"] = u"https://www.furaffinity.net/user/{user}".format(user=_furaffinity(user))
            elif t == "sf":
                link.attrib["href"] = u"https://{user}.sofurry.com/".format(user=_sofurry(user))
            else:
                continue

            if not link.text or link.text == href:
                link.text = user

    for parent in fragment.findall(".//*[img]"):
        for image in list(parent):
            if image.tag != "img":
                continue

            src = image.get("src")

            if src:
                t, _, user = src.partition(":")

                if t != "user":
                    if images_left:
                        images_left -= 1
                    else:
                        i = list(parent).index(image)
                        link = etree.Element(u"a")
                        link.tail = image.tail
                        src = image.get("src")

                        if src:
                            link.set(u"href", src)
                            link.text = image.attrib.get("alt", src)

                        parent[i] = link

                    continue

                image.set(u"src", u"/~{user}/avatar".format(user=login_name(user)))

                link = etree.Element(u"a")
                link.set(u"href", u"/~{user}".format(user=login_name(user)))
                link.set(u"class", u"user-icon")
                parent.insert(list(parent).index(image), link)
                parent.remove(image)
                link.append(image)
                link.tail = image.tail

                if "alt" in image.attrib and image.attrib["alt"]:
                    image.tail = u" "
                    label = etree.SubElement(link, u"span")
                    label.text = image.attrib["alt"]
                    del image.attrib["alt"]
                else:
                    image.tail = None
                    image.set(u"alt", user)

    add_user_links(fragment, None, True)

    defang(fragment)

    return fragment


def markdown(target, image=False):
    fragment = _markdown_fragment(target, image)
    return html.tostring(fragment, encoding=unicode)[5:-6]  # <div>...</div>


def _itertext_spaced(element):
    if element.text:
        yield element.text

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
    fragment = _markdown_fragment(markdown_text, image=False)
    text = _normalize_whitespace("".join(_itertext_spaced(fragment)))

    if len(text) <= length:
        return text
    else:
        return text[:length - 1].rstrip() + "…"


def markdown_link(title, url):
    title = title.replace('[', '\\[').replace(']', '\\]')
    return '[%s](%s)' % (title, url)

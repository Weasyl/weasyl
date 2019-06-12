# encoding: utf-8
from __future__ import unicode_literals

import re
from collections import namedtuple
from xml.dom.minidom import Node, NodeList, _get_elements_by_tagName_helper

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import html5lib
import misaka
from html5lib.constants import entities
from html5lib.serializer import HTMLSerializer

from .compat import xrange
from .defang import DefangFilter
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
    <
        (?P<type>!~|[!~])
        (?P<username>[a-z0-9_]+)
    >
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


def _strip_outer_tag(html):
    match = locatestarttagend.match(html)
    start_tag_end = match.end()
    end_tag_start = html.rindex("<")
    return html[:start_tag_end + 1], html[start_tag_end + 1:end_tag_start], html[end_tag_start:]


class WeasylRenderer(misaka.HtmlRenderer):
    # Render Markdown in HTML
    def block_html(self, raw_html):
        if raw_html.startswith("<!--"):
            return raw_html
        start, stripped, end = _strip_outer_tag(raw_html)
        return "".join([start, _markdown(stripped).rstrip(), end])

    # Respect start of ordered lists
    def list(self, text, ordered, prefix):
        if prefix:
            return '<ol start="{start}">{text}</ol>'.format(
                start=prefix,
                text=text,
            )
        else:
            return "<ul>{text}</ul>".format(
                text=text,
            )


def _markdown(target):
    renderer = WeasylRenderer(MISAKA_FORMAT)
    markdown = misaka.Markdown(renderer, MISAKA_EXT)
    return markdown.render(target)


def _create_link(document, t, username):
    link = document.createElement("a")
    link.setAttribute("href", "/~" + login_name(username))

    if t == "~":
        link.appendChild(document.createTextNode(username))
    else:
        link.setAttribute("class", "user-icon")

        image = document.createElement("img")
        image.setAttribute("src", "/~{username}/avatar".format(username=login_name(username)))
        link.appendChild(image)

        if t == "!":
            image.setAttribute("alt", username)
        else:
            image.setAttribute("alt", "")
            link.appendChild(document.createTextNode(" "))
            label = document.createElement("span")
            label.appendChild(document.createTextNode(username))
            link.appendChild(label)

    return link


def _add_user_links(element):
    document = element.ownerDocument

    for i in xrange(element.childNodes.length - 1, -1, -1):
        child = element.childNodes[i]

        if child.nodeType == Node.TEXT_NODE:
            parts = []
            last_end = 0
            text = child.nodeValue

            for m in USER_LINK.finditer(text):
                t, username = m.group("type", "username")

                link = _create_link(document, t, username)

                start, end = m.span()
                parts.append((text[last_end:start], link))
                last_end = end

            if parts:
                for head, link in parts:
                    if head:
                        element.insertBefore(document.createTextNode(head), child)

                    if link is not None:
                        element.insertBefore(link, child)

                if last_end == len(text):
                    element.removeChild(child)
                else:
                    element.replaceChild(document.createTextNode(text[last_end:]), child)
        elif child.nodeType == Node.ELEMENT_NODE and child.tagName not in ("a", "pre", "code"):
            _add_user_links(child)


_UserLink = namedtuple("_UserLink", ["href", "text"])


def _get_user_link(href):
    t, _, user = href.partition(":")

    if t == "user":
        result = "/~{user}".format(user=login_name(user))
    elif t == "da":
        result = "https://{user}.deviantart.com/".format(user=_deviantart(user))
    elif t == "ib":
        result = "https://inkbunny.net/{user}".format(user=_inkbunny(user))
    elif t == "fa":
        result = "https://www.furaffinity.net/user/{user}".format(user=_furaffinity(user))
    elif t == "sf":
        result = "https://{user}.sofurry.com/".format(user=_sofurry(user))
    else:
        return None

    return _UserLink(result, user)


def _empty(node):
    while node.hasChildNodes():
        node.removeChild(node.lastChild)


def _add_nofollows(stream):
    for token in stream:
        if token["type"] == "StartTag":
            href = token["data"].get((None, "href"))

            if href is not None:
                url = urlparse(href)

                if url.hostname not in (None, "www.weasyl.com", "weasyl.com", "forums.weasyl.com"):
                    token["data"][(None, "rel")] = "nofollow"

        yield token


def _safe_markdown_stream(target):
    rendered = _markdown(target)
    fragment = html5lib.parseFragment(rendered, treebuilder="dom")
    fragment.normalize()

    document = fragment.ownerDocument
    links = _get_elements_by_tagName_helper(fragment, "a", NodeList())

    for link in links:
        href = link.getAttribute("href")

        if href:
            user_link = _get_user_link(href)

            if user_link is not None:
                link.setAttribute("href", user_link.href)

                if link.childNodes.length == 0 or (
                    link.childNodes.length == 1 and
                    link.firstChild.nodeType == Node.TEXT_NODE and
                    link.firstChild.nodeValue == href
                ):
                    _empty(link)
                    link.appendChild(document.createTextNode(user_link.text))

    del links

    images = _get_elements_by_tagName_helper(fragment, "img", NodeList())

    for image in images:
        src = image.getAttribute("src")
        alt = image.getAttribute("alt")

        if src:
            t, _, user = src.partition(":")

            if t != "user":
                link = document.createElement("a")
                link.setAttribute("href", src)
                link.appendChild(document.createTextNode(alt or src))
                image.parentNode.replaceChild(link, image)
                continue

            image.setAttribute("src", "/~{user}/avatar".format(user=login_name(user)))

            link = document.createElement("a")
            link.setAttribute("href", "/~{user}".format(user=login_name(user)))
            link.setAttribute("class", "user-icon")
            image.parentNode.replaceChild(link, image)
            link.appendChild(image)

            if alt:
                label = document.createElement("span")
                label.appendChild(document.createTextNode(alt))

                link.appendChild(document.createTextNode(" "))
                link.appendChild(label)

                image.setAttribute("alt", "")
            else:
                image.setAttribute("alt", user)

    _add_user_links(fragment)

    unsafe_stream = html5lib.getTreeWalker("dom")(fragment)

    safe_stream = DefangFilter(unsafe_stream)

    return _add_nofollows(safe_stream)


def _chomp(s):
    return s[:-1] if s.endswith("\n") else s


def markdown(target):
    stream = _safe_markdown_stream(target)
    serializer = HTMLSerializer(quote_attr_values="always", omit_optional_tags=False, alphabetical_attributes=True)
    return _chomp(serializer.render(stream))


def _itertext_spaced(stream):
    for token in stream:
        tt = token["type"]

        if tt in ("Characters", "SpaceCharacters"):
            yield token["data"]
        elif tt in ("StartTag", "EndTag"):
            if token["name"] in _EXCERPT_BLOCK_ELEMENTS:
                yield " "
        elif tt == "Entity":
            key = token["name"] + ";"
            yield entities.get(key, "&" + key)


def _normalize_whitespace(text):
    return re.sub(r"\s+", " ", text.strip())


def markdown_excerpt(markdown_text, length=300):
    stream = _safe_markdown_stream(markdown_text)
    text = _normalize_whitespace("".join(_itertext_spaced(stream)))

    if len(text) <= length:
        return text
    else:
        return text[:length - 1].rstrip() + "…"


def markdown_link(title, url):
    title = title.replace("[", "\\[").replace("]", "\\]")
    return "[%s](%s)" % (title, url)

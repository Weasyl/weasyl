"""
HTML defanging.

:py:func:`.defang` is the primary export of this module.
"""

import re
from dataclasses import dataclass
from typing import Optional

from ada_url import URL

allowed_tags = {
    "section", "nav", "article", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "footer", "address",
    "p", "hr", "pre", "blockquote", "ol", "ul", "li",
    "dl", "dt", "dd", "figure", "figcaption", "div",
    "em", "strong", "small", "s", "cite", "q", "dfn",
    "abbr", "time", "code", "var", "samp", "kbd",
    "sub", "sup", "i", "b", "u", "mark",
    "ruby", "rt", "rp", "bdi", "bdo", "span", "br", "wbr",
    "del",
    "table", "caption",
    "tbody", "thead", "tfoot", "tr", "td", "th",
    "a", "img"
}
"""
All allowed HTML tag names.

Any HTML tags in the *fragment* passed to :py:func:`.defang` not in this list
will be removed.
"""

allowed_attributes = {
    "title", "alt", "colspan", "rowspan", "start", "type", "width", "height"
}
"""
Almost all allowed HTML tag attribute names.

Notably, not listed here is special permission for ``href``, which is only
allowed on ``a`` tags, ``src``, which is only allowed on ``img`` tags, and
``class``, which is allowed on any tag.

Otherwise, any HTML tag attributes in the *fragment* passed to
:py:func:`.defang` not in this list will be removed.
"""

allowed_schemes = {
    "http:", "https:", "mailto:", "irc:", "ircs:", "magnet:"
}
"""
All allowed URL schemes.

URLs passed in the *fragment* to :py:func:`.defang` are only permitted as
``href`` attributes on ``a`` tags and ``src`` attributes on ``img`` tags. Any
URL in either attribute value which does not have a scheme in this list will be
removed.
"""

allowed_classes = {
    "align-left", "align-center", "align-right", "align-justify",
    "user-icon",
    "invalid-markup",
}
"""
All allowed CSS classes.

Any HTML ``class`` passed in the *fragment* to :py:func:`.defang` that isn't in
this list will be removed.
"""

ALLOWED_STYLE = re.compile(r"""
\A \s*
color: \s* (?:
  \#[0-9a-f]{3}
| \#[0-9a-f]{6}
)
(?: \s* ; )?
\s* \Z
""", re.X | re.I)


_C0_OR_SPACE = "".join(map(chr, range(0x21)))
_TAB_OR_NEWLINE = re.compile(r"[\t\n\r]")


_DUMMY_URL_BASE = "https://h/"


@dataclass(frozen=True, slots=True)
class CleanHref:
    """
    The cleaned value of an HTML link, like an `<a>`'s `href` or an `<img>`'s `src`.

    See <https://url.spec.whatwg.org>.

    Ignoring URL-query string and URL-fragment string parts,
    - absolute-URL-with-fragment strings with permitted schemes are reserialized
    - scheme-relative-special-URL strings are resolved to `https:`
    - path-absolute-URL strings are reserialized
    - other valid URL strings (including path-relative-URL strings, even if empty) are rejected
    - invalid URL strings that don't fail to parse take one of the above paths

    Note: In the case of invalid URL strings, the cleaned value is not necessarily the value that a browser would use when parsing the original link in the context of a document! `URL("http:foo.test") == URL("http:foo.test", "https://bar.test") != URL("http:foo.test", "http://bar.test")`.
    """

    value: str
    hostname: str | None

    @classmethod
    def try_from(cls, s: str) -> Optional["CleanHref"]:
        # Apply part of the URL parsing algorithm ahead of time for later check for path-absolute relative and scheme-relative URLs.
        s = _TAB_OR_NEWLINE.sub("", s.strip(_C0_OR_SPACE))

        try:
            # NOTE: This can also raise `UnicodeDecodeError`. User input should never be able to trigger that condition, so the exception is propagated instead of producing `None`.
            u = URL(s)
        except ValueError:
            pass
        else:
            return cls(
                value=u.href,
                hostname=u.hostname,
            ) if u.protocol in allowed_schemes else None

        if not s.startswith(("/", "\\")):
            # either a path-relative URL, which is hard to support in a way that makes sense and is usually the result of a user mistake (e.g. `<a href="example.com">`), or an invalid URL
            return None

        try:
            u = URL(s, _DUMMY_URL_BASE)
        except ValueError:
            return None

        if len(s) >= 2 and s[1] in ["/", "\\"]:
            # a scheme-relative URL
            assert u.protocol == "https:"

            return cls(
                value=u.href,
                hostname=u.hostname,
            )

        return cls(
            value=u.pathname,
            hostname=None,
        )


def defang(fragment):
    """
    Remove potentially harmful attributes and elements from an HTML fragment.

    Currently, that means:

    - Each descendant element's tag must be in a whitelist of tags.
    - ``a`` tags with an ``href`` attribute must have their ``href`` URL's
      scheme in a whitelist of URL schemes. Additionally, links to non-Weasyl
      websites will have a ``rel="nofollow ugc"`` attribute added to the tag.
    - ``img`` tags with an ``src`` attribute must have their ``src`` URL's
      scheme in a whitelist of URL schemes.
    - Any element with a ``style`` attribute is only permitted a CSS ``color``
      declaration of a hex color value, and no other CSS properties.
    - Any element with a ``class`` attribute is only permitted classes in a
      whitelist of CSS classes.
    - Any attributes on an element not mentioned above must be in a whitelist
      of attribute names.

    Parameters:
        fragment: An lxml ``Element``.

    Returns:
        ``None``, as modification is done in-place on *fragment*.
    """
    unwrap = []

    for child in fragment:
        if child.tag not in allowed_tags:
            unwrap.append(child)

        extend_attributes = []

        for key, value in child.items():
            # `value_stripped` is a correct thing to do according to the WHATWG URL spec (but not the only possible validation error, and not all are handled here yet). It also works around CVE-2023-24329 while on Python <3.10.12.
            if key == "href" and child.tag == "a" and (c := CleanHref.try_from(value)) is not None:
                extend_attributes.append((key, c.value))

                if c.hostname not in (None, "www.weasyl.com", "weasyl.com"):
                    extend_attributes.append(("rel", "nofollow ugc"))
            elif key == "src" and child.tag == "img" and (c := CleanHref.try_from(value)) is not None:
                extend_attributes.append((key, c.value))
            elif key == "style" and ALLOWED_STYLE.match(value):
                pass
            elif key == "class":
                child.set("class", " ".join(set(value.split()) & allowed_classes))
            elif key not in allowed_attributes:
                del child.attrib[key]

        for key, value in extend_attributes:
            child.set(key, value)

        defang(child)

    for child in unwrap:
        child.drop_tag()

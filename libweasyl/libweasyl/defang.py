"""
HTML defanging.
"""

from __future__ import unicode_literals

import re

from html5lib.constants import namespaces
from html5lib.filters import sanitizer

allowed_elements = frozenset((namespaces["html"], tag) for tag in [
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
])
"""
All allowed HTML tags.
"""

allowed_attributes = frozenset([
    (None, "href"),
    (None, "src"),
    (None, "style"),
    (None, "class"),
    (None, "title"),
    (None, "alt"),
    (None, "colspan"),
    (None, "rowspan"),
    (None, "start"),
    (None, "type"),
    (None, "width"),
    (None, "height"),
])
"""
All allowed HTML attributes.
"""

allowed_protocols = frozenset([
    "http", "https", "mailto", "irc", "ircs", "magnet",
    "data",  # disallowed via allowed_content_types, working around https://github.com/html5lib/html5lib-python/pull/412
])
"""
All allowed URL schemes.
"""

allowed_classes = frozenset([
    None,
    "align-left",
    "align-center",
    "align-right",
    "align-justify",
    "user-icon",
])
"""
All allowed CSS classes.
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


class DefangFilter(sanitizer.Filter):
    def __init__(self, stream):
        super(DefangFilter, self).__init__(
            stream,
            allowed_elements=allowed_elements,
            allowed_attributes=allowed_attributes,
            allowed_protocols=allowed_protocols,
            allowed_content_types=frozenset(),
        )

    def sanitize_css(self, style):
        return style if ALLOWED_STYLE.match(style) else ""

    def allowed_token(self, token):
        token = super(DefangFilter, self).allowed_token(token)

        if token and "data" in token:
            if token["data"].get((None, "class")) not in allowed_classes:
                del token["data"][(None, "class")]

        return token

"""
HTML defanging.

:py:func:`.defang` is the primary export of this module.
"""

import re
from urllib.parse import urlparse

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
    "", "http", "https", "mailto", "irc", "ircs", "magnet"
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
    "user-icon"
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


def get_scheme(url):
    """
    Get the scheme from a URL, if the URL is valid.

    Parameters:
        url: A :term:`native string`.

    Returns:
        The scheme of the url as a :term:`native string`, or ``None`` if the
        URL was invalid.
    """
    try:
        return urlparse(url).scheme
    except ValueError:
        return None


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
            if key == "href" and child.tag == "a" and get_scheme(value) in allowed_schemes:
                url = urlparse(value)

                if url.hostname not in (None, "www.weasyl.com", "weasyl.com"):
                    extend_attributes.append(("rel", "nofollow ugc"))
            elif key == "src" and child.tag == "img" and get_scheme(value) in allowed_schemes:
                pass
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

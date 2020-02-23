"""
Utilities for dealing with HTML.

Specifically, utilities for creating HTML and utilities for removing HTML.
"""


try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser


def strip_html(markdown):
    """
    Strip HTML tags from a markdown string.

    Entities present in the markdown will be escaped.

    Parameters:
        markdown: A :term:`native string` to be stripped and escaped.

    Returns:
        An escaped, stripped :term:`native string`.
    """
    class Parser(HTMLParser):
        text_parts = []

        def handle_data(self, data):
            self.text_parts.append(
                data
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        def handle_entityref(self, name):
            self.text_parts.append("&" + name + ";")

        def handle_charref(self, name):
            self.text_parts.append("&#" + name + ";")

    parser = Parser()
    parser.feed(markdown)
    return "".join(parser.text_parts)

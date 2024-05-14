"""
Utilities for dealing with HTML.

Specifically, utilities for creating HTML and utilities for removing HTML.
"""

import json
from html.parser import HTMLParser


class _HtmlToText(HTMLParser):

    def __init__(self, handle_data):
        super().__init__()
        self.handle_data = handle_data

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            alt = next((value for key, value in attrs if key == "alt"), None)

            if alt:
                self.handle_data(f"[{alt}]")


def html_to_text(markdown: str) -> str:
    """
    Convert HTML to a plain text representation suitable for summaries.
    """
    text_parts = []
    parser = _HtmlToText(text_parts.append)
    parser.feed(markdown)
    parser.close()
    return " ".join("".join(text_parts).split())


def inline_json(obj):
    """
    Format a python object as JSON for inclusion in HTML.

    Parameters:
        obj: A python object that can be converted to JSON.

    Returns:
        An escaped :term:`native string` of JSON.
    """
    return json.dumps(obj).replace("</", r"<\/").replace("<!--", r"<\!--")

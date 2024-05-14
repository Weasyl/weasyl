"""
Utilities for dealing with HTML.

Specifically, utilities for creating HTML and utilities for removing HTML.
"""

import json
from html.parser import HTMLParser


def strip_html(markdown: str) -> str:
    """
    Strip HTML tags and resolve character references in a markdown string.
    """
    text_parts = []
    parser = HTMLParser()
    parser.handle_data = text_parts.append
    parser.feed(markdown)
    parser.close()
    return "".join(text_parts)


def inline_json(obj):
    """
    Format a python object as JSON for inclusion in HTML.

    Parameters:
        obj: A python object that can be converted to JSON.

    Returns:
        An escaped :term:`native string` of JSON.
    """
    return json.dumps(obj).replace("</", r"<\/").replace("<!--", r"<\!--")

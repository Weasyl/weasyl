import json
from typing import Any


def inline_json(obj: Any) -> str:
    """
    Format a python object as JSON for inclusion in HTML.

    Parameters:
        obj: A python object that can be converted to JSON.

    Returns:
        An escaped :term:`native string` of JSON.
    """
    return json.dumps(obj).replace("</", r"<\/").replace("<!--", r"<\!--")

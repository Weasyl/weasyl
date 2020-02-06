from __future__ import absolute_import

import re
import string
import urlparse

from libweasyl.cache import region

from weasyl import define as d


_BANDCAMP_EMBED = re.compile(r"(album|track)=(\d+)")


_OEMBED_MAP = {
    "youtube": "https://www.youtube.com/oembed?url=%s&maxwidth=640&maxheight=360",
    "vimeo": "https://vimeo.com/api/oembed.json?url=%s&maxwidth=400&maxheight=300",
    "soundcloud": "https://soundcloud.com/oembed?format=json&url=%s",
    "vine": "https://vine.co/oembed.json?url=%s&maxwidth=600&maxheight=600",
    "sketchfab": "https://sketchfab.com/oembed?url=%s&maxwidth=640&maxheight=480",
}


def _service(link):
    """
    Returns the content service name based on the URL provided.
    """
    url = urlparse.urlsplit(link)
    domain = "." + url.netloc.lower()

    if domain.endswith((".youtube.com", ".youtu.be")):
        return "youtube"
    elif domain.endswith(".vimeo.com"):
        return "vimeo"
    elif domain.endswith(".bandcamp.com"):
        return "bandcamp"
    elif domain.endswith(".soundcloud.com"):
        return "soundcloud"
    elif domain.endswith(".vine.co"):
        return "vine"
    elif domain.endswith(".sketchfab.com"):
        return "sketchfab"


def _targetid(link):
    """
    Returns the content service's identifier based on the URL provided.
    """
    service = _service(link)

    if service in _OEMBED_MAP:
        # Validate with oEmbed
        link = link.strip()
        alpha = string.printable
    elif service == "bandcamp":
        content = d.http_get(link).text
        match = _BANDCAMP_EMBED.search(content)

        if match:
            return match.groups()
        else:
            return None
    else:
        return None

    for i in range(len(link)):
        if link[i] not in alpha:
            return link[:i]

    return d.plaintext(link)


@region.cache_on_arguments(expiration_time=60 * 60 * 24)
@d.record_timing
def _embed_json(service, targetid):
    """
    Returns oEmbed JSON for a given URL and service
    """
    if service in _OEMBED_MAP:
        return d.http_get(_OEMBED_MAP[service] % targetid).json()


def html(link):
    """
    Returns the HTML code to be used in a template for a given identifier.
    """
    targetid, service = _targetid(link), _service(link)

    if targetid:
        if service in _OEMBED_MAP:
            try:
                return _embed_json(service, targetid)["html"]
            except (ValueError, KeyError):
                return "There was an error retrieving the embedded media"
        elif service == "bandcamp":
            return (
                '<iframe width="400" height="100" '
                'style="position:relative;display:block;width:400px;height:100px;" '
                'src="https://bandcamp.com/EmbeddedPlayer/v=2/%s=%s/size=venti/bgcol=F0F0F0/linkcol=4285BB/" '
                'allowtransparency="false" frameborder="0"></iframe>' % (targetid[0], targetid[1]))


def thumbnail(link):
    """
    Returns the URL to a thumbnail for a given identifier.
    """
    targetid, service = _targetid(link), _service(link)

    if targetid:
        if service in _OEMBED_MAP:
            try:
                return _embed_json(service, targetid)["thumbnail_url"]
            except (ValueError, KeyError):
                return None
        elif service == "bandcamp":
            # Sometime in the future, parse the HTML for the image_src meta tag
            return None

    return None


def check_valid(link):
    """
    Returns True if a given URL is embeddable.
    """
    targetid, service = _targetid(link), _service(link)

    if targetid:
        if service in _OEMBED_MAP:
            try:
                return bool(_embed_json(service, targetid)["html"])
            except (ValueError, KeyError):
                return
        elif service == "bandcamp":
            return True

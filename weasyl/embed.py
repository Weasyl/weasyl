from html import escape
from html.parser import HTMLParser
import re
import string
from urllib.parse import quote as urlquote, urlsplit

from libweasyl.cache import region

from weasyl import define as d


_BANDCAMP_EMBED = re.compile(r"(album|track)=(\d+)")


_OEMBED_MAP = {
    "youtube": "https://www.youtube.com/oembed?url=%s&maxwidth=640&maxheight=360",
    "vimeo": "https://vimeo.com/api/oembed.json?url=%s&maxwidth=400&maxheight=300",
    "soundcloud": "https://soundcloud.com/oembed?format=json&url=%s",
    "sketchfab": "https://sketchfab.com/oembed?url=%s&maxwidth=640&maxheight=480",
    "bluesky": "https://embed.bsky.app/oembed?url=%s",
}


class BlueskyAtUriExtractor(HTMLParser):
    """Just enough of a parser to extract the at-uri from a Bluesky oEmbed"""
    def __init__(self):
        self.at_uri = None
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "blockquote":
            for key, value in attrs:
                if key == "data-bluesky-uri":
                    self.at_uri = value


def _service(link):
    """
    Returns the content service name based on the URL provided.
    """
    url = urlsplit(link)
    domain = "." + url.netloc.lower()

    if domain.endswith((".youtube.com", ".youtu.be")):
        return "youtube"
    elif domain.endswith(".vimeo.com"):
        return "vimeo"
    elif domain.endswith(".bandcamp.com"):
        return "bandcamp"
    elif domain.endswith(".soundcloud.com"):
        return "soundcloud"
    elif domain.endswith(".sketchfab.com"):
        return "sketchfab"
    elif domain.endswith(".bsky.app"):
        return "bluesky"


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

    return link


@region.cache_on_arguments(expiration_time=60 * 60 * 24)
@d.record_timing
def _embed_json(service, targetid):
    """
    Returns oEmbed JSON for a given URL and service
    """
    return d.http_get(_OEMBED_MAP[service] % (urlquote(targetid),)).json()


@region.cache_on_arguments(expiration_time=60 * 60 * 24)
@d.record_timing
def _embed_bluesky(targetid: str) -> str:
    """
    Get the best possible HTML for displaying this Bluesky-hosted video.

    Attempt to generate a direct video element, if possible. If this is not
    possible, fall back to Bluesky's oEmbed output. As of writing, the oEmbed
    output does not directly embed a video, instead providing a clickable
    thumbnail of the video that then leads to Bluesky.
    """
    oembed_html = _embed_json("bluesky", targetid)["html"]

    extractor = BlueskyAtUriExtractor()
    extractor.feed(oembed_html)

    if not extractor.at_uri:
        return oembed_html

    detail_uri = f"https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris={extractor.at_uri}"

    try:
        detail_json = d.http_get(detail_uri).json()
        playlist_uri: str = escape(detail_json["posts"][0]["embed"]["playlist"])
    except Exception:
        return oembed_html

    out = f'<video id="hls-video" src="{playlist_uri}" controls></video>'
    out += '<p id="video-error" hidden>There was an error playing the embedded media</p>'

    return out


def html(link):
    """
    Returns the HTML code to be used in a template for a given identifier.
    """
    targetid, service = _targetid(link), _service(link)

    if not targetid:
        return

    try:
        if service == "bandcamp":
            return (
                '<iframe width="400" height="100" '
                'style="position:relative;display:block;width:400px;height:100px;" '
                'src="https://bandcamp.com/EmbeddedPlayer/v=2/%s=%s/size=venti/bgcol=F0F0F0/linkcol=4285BB/" '
                'allowtransparency="false" frameborder="0"></iframe>' % (targetid[0], targetid[1]))
        elif service == "bluesky":
            return _embed_bluesky(targetid)
        elif service in _OEMBED_MAP:
            return _embed_json(service, targetid)["html"]
    except (ValueError, KeyError):
        return "There was an error retrieving the embedded media"


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

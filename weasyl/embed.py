import functools
import os
import re
from abc import abstractmethod
from dataclasses import dataclass
from ssl import TLSVersion
from typing import Literal
from typing import Protocol
from typing import cast
from urllib.parse import quote as urlquote

import requests
import urllib3.util
from markupsafe import Markup
from requests import RequestException
from urllib3 import PoolManager
from urllib3.contrib.socks import SOCKSProxyManager
from urllib3.exceptions import HTTPError

from libweasyl.cache import region

from weasyl import define as d
from weasyl.config import config_obj
from weasyl.define import HttpUrl


OembedService = Literal[
    "youtube",
    "vimeo",
    "soundcloud",
    "sketchfab",
]

Service = OembedService | Literal["bandcamp"]

BandcampType = Literal["album", "track"]


_BANDCAMP_EMBED = re.compile(rb"(album|track)=(\d+)")


_OEMBED_MAP: dict[OembedService, str] = {
    "youtube": "https://www.youtube.com/oembed?url=%s&maxwidth=640&maxheight=360",
    "vimeo": "https://vimeo.com/api/oembed.json?url=%s&maxwidth=400&maxheight=300",
    "soundcloud": "https://soundcloud.com/oembed?format=json&url=%s",
    "sketchfab": "https://sketchfab.com/oembed?url=%s&maxwidth=640&maxheight=480",
}

_SERVICE_NAMES: dict[Service, str] = {
    "youtube": "YouTube",
    "vimeo": "Vimeo",
    "soundcloud": "SoundCloud",
    "sketchfab": "Sketchfab",
    "bandcamp": "Bandcamp",
}

user_agent = config_obj.get("outgoing_requests", "embed_user_agent")


# don’t really want structural subtyping here, but making `Embed` an `abc.ABC` will cause `dataclass` to think `embedlink` and `thumbnail_url` have default values, even when they’re defined with `field()`
class Embed(Protocol):

    @property
    @abstractmethod
    def embedlink(self) -> HttpUrl:
        """The cleaned link to the content being embedded, to store in the database, serve to users as an HTML link, and serve to API consumers in the `"embedlink"` field."""
        ...

    @property
    @abstractmethod
    def thumbnail_url(self) -> str | None:
        ...

    @property
    @abstractmethod
    def safer_html(self) -> Markup:
        ...


@dataclass(frozen=True, slots=True)
class Oembed:
    embedlink: HttpUrl
    service: OembedService
    untrusted_html: str
    width: int | Literal["100%"]  # Soundcloud serves "100%"×400; oEmbed spec is ambiguous on this
    height: int
    thumbnail_url: str | None

    @property
    def safer_html(self) -> Markup:
        return Markup("""<div class="embed content" style="width:{width};height:{height}px"><a class="embed-link button" data-service="{service}" data-untrusted-html="{untrusted_html}" href="{href}">View on {service_name}</a></div>""").format(
            untrusted_html=self.untrusted_html,
            service=self.service,
            width="100%" if self.width == "100%" else f"{self.width}px",
            height=self.height,
            href=self.embedlink.href,
            service_name=_SERVICE_NAMES[self.service],
        )


@dataclass(frozen=True, slots=True)
class BandcampEmbed:
    embedlink: HttpUrl
    type: BandcampType
    id: int

    @property
    def thumbnail_url(self) -> None:
        # TODO: Sometime in the future, parse the HTML for the image_src meta tag
        return None

    @property
    def safer_html(self) -> Markup:
        return Markup("""<div class="embed content embed-bandcamp"><a class="embed-link button" data-service="bandcamp" data-bandcamp-id="{type}={id}" href="{href}">View on Bandcamp</a></div>""").format(
            type=self.type,
            id=self.id,
            href=self.embedlink.href,
        )


@dataclass(frozen=True, slots=True)
class FailedEmbed:
    """
    An embed whose required information for embedding failed to load, but which can be still be rendered as a valid link.
    """

    embedlink: HttpUrl
    service: Service

    @property
    def thumbnail_url(self) -> None:
        return None

    @property
    def safer_html(self) -> Markup:
        return Markup("""<div class="embed content embed-failed"><a class="embed-link button" href="{href}">View on {service_name}</a></div>""").format(
            href=self.embedlink.href,
            service_name=_SERVICE_NAMES[self.service],
        )


class EmbedError(Exception):
    pass


class UnrecognizedLink(EmbedError):
    pass


class UpstreamFailure(EmbedError):
    failed_embed: FailedEmbed

    def __init__(self, *args, failed_embed: FailedEmbed):
        super().__init__(*args)
        self.failed_embed = failed_embed


def _get_service(url: HttpUrl) -> Service | None:
    dhost = "." + url.host
    del url

    if dhost.endswith((".youtube.com", ".youtu.be")):
        return "youtube"
    if dhost.endswith(".vimeo.com"):
        return "vimeo"
    if dhost.endswith(".bandcamp.com"):
        return "bandcamp"
    if dhost.endswith(".soundcloud.com"):
        return "soundcloud"
    if dhost.endswith(".sketchfab.com"):
        return "sketchfab"

    return None


def load(url: HttpUrl) -> Embed:
    service = _get_service(url)
    if service is None:
        raise UnrecognizedLink()

    if service == "bandcamp":
        [(type_, id_)] = _fetch_bandcamp_embed(url).items()

        return BandcampEmbed(
            embedlink=url,
            type=type_,
            id=id_,
        )

    failed_embed = FailedEmbed(
        embedlink=url,
        service=service,
    )

    try:
        data = _embed_json(service, url.href)
    except RequestException as e:
        raise UpstreamFailure("upstream request failed", failed_embed=failed_embed) from e

    if (
        isinstance(data, dict)
        and isinstance(untrusted_html := data.get("html"), str)
        and isinstance(thumbnail_url := data.get("thumbnail_url"), (type(None), str))
        and (isinstance(width := data.get("width"), int) or width == "100%")
        and isinstance(height := data.get("height"), int)
    ):
        return Oembed(
            embedlink=url,
            service=service,
            untrusted_html=untrusted_html,
            width=width,
            height=height,
            thumbnail_url=thumbnail_url,
        )

    raise UpstreamFailure("unexpected oEmbed response shape", failed_embed=failed_embed)


@region.cache_on_arguments(expiration_time=60 * 60 * 24)
@d.record_timing
def _embed_json(service: OembedService, targetid: str):
    """
    Returns oEmbed JSON for a given URL and service
    """
    resp = requests.get(
        _OEMBED_MAP[service] % (urlquote(targetid),),
        headers={
            "User-Agent": user_agent,
        },
    )
    resp.raise_for_status()
    return resp.json()


# Less broadly compatible proxy discovery in part because of <https://docs.python.org/3/library/urllib.request.html#module-urllib.request>:
# > Warning: On macOS it is unsafe to use this module in programs using `os.fork()` because the `getproxies()` implementation for macOS uses a higher-level system API.
# (Gunicorn forks.) We only really care about Linux anyway.
_https_proxy = os.environ.get("https_proxy")
_create_https_manager = (
    functools.partial(SOCKSProxyManager, _https_proxy) if _https_proxy
    else PoolManager)
del _https_proxy


# Based on the default context initialization (https://github.com/urllib3/urllib3/blob/2.4.0/src/urllib3/connection.py#L872).
# Non-default ciphers (via TLSv1.3) to work around Bandcamp’s blocking of urllib3 (https://github.com/urllib3/urllib3/issues/3439#issuecomment-2306400349).
_ssl_context = urllib3.util.create_urllib3_context(
    ssl_minimum_version=TLSVersion.TLSv1_3,
)
_ssl_context.load_default_certs()


# Bandcamp embed information can be cached forever, since it’s just a type and id – unless the object the URL refers to is replaced with a new one. There’s no single right thing to do in that situation, and other embeds have a similar issue (24 hours is pretty long). Refreshing only when a new post with the same URL is created or when an edit is saved makes some sense, but could affect other submissions, since the cache key is the URL.
# TODO: save this response in the database alongside the embed link and associate it with a single submission
# TODO: cache failures for a short time
# TODO: distributed lock
@region.cache_on_arguments(to_str=lambda url: url.href)
def _fetch_bandcamp_embed(url: HttpUrl) -> dict[BandcampType, int]:
    with _create_https_manager(ssl_context=_ssl_context) as manager:
        try:
            # Ensure that
            # - we always use HTTPS, even if the user specified `http:`
            # - we only need to resolve and connect to one domain name (improves cache effectiveness, doesn’t communicate what’s being accessed over DNS or plaintext SNI unnecessarily)
            # - we know where the request is going (maybe there are special-case subdomains that resolve to something else; we don’t want users providing one of these and causing us to connect to an unexpected place)
            # We don’t really want a pool manager, but it’s the only public/recommended API for proxies in urllib3. This context manager closes the pool right away.
            with manager.connection_from_host("bandcamp.com", scheme="https") as pool:
                resp = pool.request("GET", url.pathname, headers={
                    "Host": url.hostname,  # not a good way to do this (would not be compatible with HTTP/2), but it’s the documented way (https://urllib3.readthedocs.io/en/stable/advanced-usage.html#custom-sni-hostname)
                    "User-Agent": user_agent,
                })

            if not (200 <= resp.status < 300):
                raise HTTPError(f"failure response code ({resp.status})")
        except HTTPError as e:
            raise UpstreamFailure(
                "upstream request failed",
                failed_embed=FailedEmbed(
                    embedlink=url,
                    service="bandcamp",
                ),
            ) from e

    match = _BANDCAMP_EMBED.search(resp.data)
    if match:
        type_ = cast(BandcampType, match.group(1).decode())
        # ideally, this would be a tuple, but the current JSON-based cache system would turn that into a list
        return {type_: int(match.group(2))}

    raise UpstreamFailure(
        "no album or track found in response",
        failed_embed=FailedEmbed(
            embedlink=url,
            service="bandcamp",
        ),
    )

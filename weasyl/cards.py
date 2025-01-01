# An intermediate refactoring step between old content + media (here, just the thumbnails) retrieval and future nice types.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial
from typing import Any
from typing import Callable
from typing import Iterable
from typing import TypedDict

from libweasyl.legacy import get_sysname
from libweasyl.text import slug_for
from libweasyl.text import summarize


# too many keys to `TypedDict` right now
Cardable = Mapping[str, Any]


# `_FileExtraKeys` and `File`: Python 3.10 doesn’t support `typing.NotRequired`.
# Keys: see libweasyl/models/media.py.
class _FileExtraKeys(TypedDict, total=False):
    mediaid: NotRequired[int]
    attributes: NotRequired[dict]
    file_type: NotRequired[str]
    file_url: NotRequired[str]


class File(_FileExtraKeys):
    display_url: str


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class ThumbnailFiles:
    fallback: File
    webp: File | None


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class Thumbnail:
    width: int | None
    height: int | None
    files: ThumbnailFiles


@dataclass(eq=False, frozen=True, slots=True)
class Avatar:
    file: File

    # TODO: replace with correct dimensions once avatar lists use a different container
    @property
    def width(self) -> int:
        return 120

    @property
    def height(self) -> int:
        return 120


# TODO: different classes for different types of card
@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class Card:
    contype: int
    rating: int
    username: str
    title: str
    caption: str
    href: str
    avatar: Avatar
    thumbnail: Thumbnail


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class DefaultThumbnails:
    visual: Thumbnail
    literary: Thumbnail
    music: Thumbnail
    multimedia: Thumbnail


def get_default_thumbnails(get_resource_path: Callable[[str], str]) -> DefaultThumbnails:
    def default_thumbnail(path: str) -> Thumbnail:
        return Thumbnail(
            width=250,
            height=250,
            files=ThumbnailFiles(
                fallback={
                    "display_url": get_resource_path(path),
                },
                webp=None,
            ),
        )

    return DefaultThumbnails(
        visual=default_thumbnail("img/default-visual.png"),
        literary=default_thumbnail("img/default-lit.png"),
        music=default_thumbnail("img/default-music.png"),
        multimedia=default_thumbnail("img/default-multi.png"),
    )


@dataclass(eq=False, frozen=True, kw_only=True, slots=True)
class Viewer:
    userid: int
    disable_custom_thumbs: bool
    default_thumbs: DefaultThumbnails

    def get_thumbnail_files(self, submission: Cardable) -> ThumbnailFiles:
        if (
            self.disable_custom_thumbs
            and submission.get('subtype', 9999) < 2000
            and submission['userid'] != self.userid
        ):
            thumb_key = 'thumbnail-generated'
        else:
            thumb_key = 'thumbnail-custom' if 'thumbnail-custom' in submission['sub_media'] else 'thumbnail-generated'

        thumb = submission['sub_media'][thumb_key][0]
        thumb_webp = None

        if thumb_key == 'thumbnail-generated':
            thumb_webp = submission['sub_media'].get('thumbnail-generated-webp', (None,))[0]

        return ThumbnailFiles(
            fallback=thumb,
            webp=thumb_webp,
        )

    def get_thumbnail(self, submission: Cardable) -> Thumbnail:
        files = self.get_thumbnail_files(submission)
        subtype = submission.get("subtype")

        # TODO: Refactor layers below this to not provide a default thumbnail. (Mind `/api/` compatibility.)
        if (
            subtype is not None
            and files.fallback["display_url"] == self.default_thumbs.visual.files.fallback["display_url"]
        ):
            if 2000 <= subtype < 3000:
                return self.default_thumbs.literary
            elif 3000 <= subtype < 3040:
                return self.default_thumbs.music
            elif 3040 <= subtype < 4000:
                return self.default_thumbs.multimedia
            else:
                return self.default_thumbs.visual

        if 'attributes' in files.fallback:
            width = files.fallback['attributes']['width']
            height = files.fallback['attributes']['height']
        else:
            width = height = None

        return Thumbnail(
            width=width,
            height=height,
            files=files,
        )

    def get_card(self, query: Cardable) -> Card:
        contype = query['contype']
        username = query['username']

        avatar = None
        thumbnail = None

        if contype in [30, 50]:
            avatar = Avatar(query['user_media']['avatar'][0])
        else:
            thumbnail = self.get_thumbnail(query)

        title = query['title']  # full name, if user
        caption = username if contype == 50 else summarize(title, 52)
        sysname = get_sysname(username)
        slug = partial(slug_for, title)

        match contype:
            case 10:
                href = "/~%s/submissions/%d/%s" % (sysname, query['submitid'], slug())
            case 20:
                href = "/character/%d/%s" % (query['charid'], slug())
            case 30:
                href = "/journal/%d/%s" % (query['journalid'], slug())
            case 40:
                href = "/submission/%d/%s" % (query['submitid'], slug())
            case 50:
                href = "/~%s" % (sysname,)
            case _:  # pragma: no cover
                raise ValueError(f"unknown contype {contype!r}")

        return Card(
            contype=contype,
            rating=query['rating'],
            username=username,
            title=title,
            caption=caption,
            href=href,
            avatar=avatar,
            thumbnail=thumbnail,
        )

    def get_cards(self, ds: Iterable[Cardable]) -> list[Card]:
        return list(map(self.get_card, ds))


def get_widths(cards: Iterable[Card]) -> str:
    """
    Gets the value of the `data-widths` attribute for a thumbnail grid.
    """
    return ",".join(str((card.thumbnail or card.avatar).width or "") for card in cards)

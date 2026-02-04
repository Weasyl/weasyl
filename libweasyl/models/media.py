from __future__ import annotations

import hashlib
import os
from collections.abc import Generator
from collections.abc import Iterable
from collections.abc import Sequence
from contextlib import contextmanager
from functools import partial
from io import BytesIO
from typing import Callable
from typing import NewType

from sqlalchemy.orm import relationship, foreign, remote, joinedload, lazyload, load_only
from sqlalchemy.sql.expression import any_

from libweasyl.files import fanout
from libweasyl.models.meta import Base
from libweasyl.models.users import Profile
from libweasyl.models import tables
from libweasyl import flash, images


DirFd = NewType("DirFd", int)


def _close_all(fds: Iterable[DirFd]) -> None:
    close_excs: list[Exception] = []

    for fd in fds:
        try:
            os.close(fd)
        except Exception as e:
            close_excs.append(e)

    if close_excs:
        # TODO: Python 3.11+: ExceptionGroup
        raise close_excs[0]


def _open_dir(path: str, dir_fd: DirFd | None = None) -> DirFd:
    return DirFd(os.open(path, os.O_RDONLY | os.O_DIRECTORY, dir_fd=dir_fd))


@contextmanager
def _makedirs_synced(root: str, components: Sequence[str]) -> Generator[DirFd]:
    """
    Open a directory `os.path.join(root, *components)` as a file descriptor, creating it and any of its ancestors (up to but not including `root`) as necessary.

    On a successful context manager exit, `fsync`s the directory and any ancestors that were modified.

    Optimistically attempts deeper `open`s first and keeps all FDs open to defer syncs to the end; `components` should be small.
    """
    first_missing = len(components)
    fd: DirFd

    # Open the deepest directory that exists, up to and including `root`.
    while True:
        try:
            fd = _open_dir(os.path.join(root, *components[:first_missing]))
            break
        except FileNotFoundError:
            if first_missing == 0:
                raise

            first_missing -= 1

    fds = [fd]

    try:
        # Create any missing directories and advance `fd` to the target.
        for i in range(first_missing, len(components)):
            os.mkdir(components[i], dir_fd=fd)
            fd = _open_dir(components[i], dir_fd=fd)
            fds.append(fd)

        yield fd

        for fd in fds:
            os.fsync(fd)
    finally:
        _close_all(fds)


class MediaItem(Base):
    __table__ = tables.media

    @classmethod
    def fetch_or_create(cls, data, file_type=None, im=None, attributes=()):
        sha256 = hashlib.sha256(data).hexdigest()
        obj = (cls.query
               .filter(cls.sha256 == sha256)
               .first())
        if obj is None:
            attributes = dict(attributes)
            if file_type is None and im is not None:
                file_type = images.image_file_type(im)
            if file_type is None:
                raise ValueError('a file type is required')
            if im is not None:
                attributes.update({'width': im.size.width, 'height': im.size.height})
            elif file_type == 'swf':
                attributes.update(flash.parse_flash_header(BytesIO(data)))
            obj = cls(sha256=sha256, file_type=file_type, attributes=attributes)

            [*dir_components, hash_filename] = obj._file_path_components

            # Write our file to the filesystem, creating the hash-named file atomically
            with _makedirs_synced(cls._base_file_path, dir_components) as dir_fd:
                temp_name = f"tmp-{os.urandom(8).hex()}"
                outfile = open(temp_name, "xb", opener=partial(os.open, dir_fd=dir_fd))

                try:
                    with outfile:
                        outfile.write(data)
                        outfile.flush()
                        os.fsync(outfile)
                except:
                    os.unlink(temp_name, dir_fd=dir_fd)
                    raise

                os.replace(temp_name, hash_filename, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)

                # Try to make sure the hash-named file is persisted before inserting it into the database
                os.fsync(dir_fd)

            cls.dbsession.add(obj)
        return obj

    # set by configure_libweasyl
    _media_link_formatter_callback: Callable[[MediaItem, str], str]
    _base_file_path: str

    def _to_dict(self):
        return {
            'mediaid': self.mediaid,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'attributes': self.attributes,
        }

    def serialize(self, *, link):
        ret = self._to_dict()
        ret['display_url'] = self._media_link_formatter_callback(self, link) or self.display_url
        return ret

    def ensure_cover_image(self, source_image):
        if self.file_type not in {'jpg', 'png', 'gif'}:
            raise ValueError('can only auto-cover image media items')

        cover = images.make_cover_image(source_image)
        if cover is source_image:
            cover_media_item = self
        else:
            cover_media_item = self.fetch_or_create(
                cover.to_buffer(format=self.file_type), file_type=self.file_type,
                im=cover)
        self.dbsession.flush()
        return cover_media_item

    @property
    def display_url(self):
        # Dodge a silly AdBlock rule
        return self.file_url.replace('media/ad', 'media/ax')

    @property
    def full_file_path(self):
        return os.path.join(self._base_file_path, *self._file_path_components)

    def as_image(self):
        return images.read(self.full_file_path.encode())

    @property
    def _file_path_components(self) -> list[str]:
        return ['static', 'media'] + fanout(self.sha256, (2, 2, 2)) + ['%s.%s' % (self.sha256, self.file_type)]

    @property
    def file_url(self):
        return '/' + '/'.join(self._file_path_components)


class _LinkMixin:
    cache_func = None

    @classmethod
    def refresh_cache(cls, identity):
        if cls.cache_func:
            cls.cache_func.refresh(identity)

    @classmethod
    def clear_link(cls, identity, link_type):
        (cls.query
         .filter(cls.link_type == link_type)
         .filter(getattr(cls, cls._identity) == identity)
         .delete('fetch'))
        cls.refresh_cache(identity)

    @classmethod
    def make_or_replace_link(cls, identity, link_type, media_item):
        obj = (cls.query
               .filter(cls.link_type == link_type)
               .filter(getattr(cls, cls._identity) == identity)
               .first())
        if obj is None:
            obj = cls(link_type=link_type)
            setattr(obj, cls._identity, identity)
            cls.dbsession.add(obj)
        obj.media_item = media_item
        cls.refresh_cache(identity)

    @classmethod
    def bucket_links(cls, identities):
        if not identities:
            return []
        q = (
            cls.get_media_query()
            .filter(getattr(cls, cls._identity) == any_(list(identities))))

        buckets = {identity: {} for identity in identities}
        for link in q:
            media_data = link.media_item.serialize(link=link)
            buckets[getattr(link, cls._identity)].setdefault(link.link_type, []).append(media_data)
        return list(buckets.values())

    @classmethod
    def register_cache(cls, func):
        cls.cache_func = staticmethod(func)
        return func


class SubmissionMediaLink(Base, _LinkMixin):
    __table__ = tables.submission_media_links

    _identity = 'submitid'

    submission = relationship('Submission')
    media_item = relationship(MediaItem)

    @classmethod
    def get_media_query(cls):
        return cls.query.options(
            joinedload(cls.media_item),
            joinedload(cls.submission).options(
                load_only('title'),
                joinedload('owner').options(
                    lazyload('profile'),
                    load_only('login_name'),
                ),
            ),
        )


class UserMediaLink(Base, _LinkMixin):
    __table__ = tables.user_media_links

    _identity = 'userid'

    user = relationship(
        Profile,
        primaryjoin=foreign(__table__.c.userid) == remote(Profile.userid))
    media_item = relationship(MediaItem)

    @classmethod
    def get_media_query(cls):
        return cls.query.options(
            joinedload(cls.media_item),
        )

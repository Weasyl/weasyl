from __future__ import division

import collections
import hashlib
from io import BytesIO
import os

from sqlalchemy.orm import relationship, foreign, remote, joinedload, object_mapper

from libweasyl.files import fanout, makedirs_exist_ok
from libweasyl.models.content import Submission
from libweasyl.models.meta import Base
from libweasyl.models.users import Profile
from libweasyl.models import tables
from libweasyl import flash, images


class MediaItem(Base):
    __table__ = tables.media
    __mapper_args__ = dict(polymorphic_on=__table__.c.media_type)

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
            obj.init_from_data(data)
            cls.dbsession.add(obj)
        return obj

    # set by configure_libweasyl
    _media_link_formatter_callback = None

    def to_dict(self):
        return {col.name: getattr(self, col.name)
                for col in object_mapper(self).mapped_table.c}

    def serialize(self, recursive=1, link=None):
        ret = self.to_dict()
        ret['display_url'] = self._media_link_formatter_callback(self, link) or self.display_url
        if recursive > 0:
            buckets = collections.defaultdict(list)
            for described_link in self.described:
                buckets[described_link.link_type].append(
                    described_link.media_item.serialize(
                        recursive=recursive - 1, link=described_link))
            ret['described'] = dict(buckets)
        else:
            ret['described'] = {}
        if 'width' in self.attributes and 'height' in self.attributes:
            ret['aspect_ratio'] = self.attributes['width'] / self.attributes['height']
        return ret

    def ensure_cover_image(self, source_image=None):
        if self.file_type not in {'jpg', 'png', 'gif'}:
            raise ValueError('can only auto-cover image media items')
        cover_link = next((link for link in self.described if link.link_type == 'cover'), None)
        if cover_link is not None:
            return cover_link.media_item

        if source_image is None:
            source_image = self.as_image()
        cover = images.make_cover_image(source_image)
        if cover is source_image:
            cover_media_item = self
        else:
            cover_media_item = fetch_or_create_media_item(
                cover.to_buffer(format=self.file_type.encode()), file_type=self.file_type,
                im=cover)
        self.dbsession.flush()
        MediaMediaLink.make_or_replace_link(self.mediaid, 'cover', cover_media_item)
        return cover_media_item

    def make_thumbnail(self, source_image=None):
        if self.file_type not in {'jpg', 'png', 'gif'}:
            raise ValueError('can only auto-thumbnail image media items')
        if source_image is None:
            source_image = self.as_image()
        thumbnail = images.make_thumbnail(source_image)
        if thumbnail is source_image:
            return self
        else:
            return fetch_or_create_media_item(
                thumbnail.to_buffer(format=self.file_type.encode()), file_type=self.file_type,
                im=thumbnail)


class DiskMediaItem(MediaItem):
    __table__ = tables.disk_media
    __mapper_args__ = dict(polymorphic_identity='disk')

    def init_from_data(self, data):
        path = ['static', 'media'] + fanout(self.sha256, (2, 2, 2)) + ['%s.%s' % (self.sha256, self.file_type)]
        self.file_path = os.path.join(*path)
        self.file_url = '/' + self.file_path
        real_path = self.full_file_path
        makedirs_exist_ok(os.path.dirname(real_path))
        with open(real_path, 'wb') as outfile:
            outfile.write(data)

    @property
    def display_url(self):
        # Dodge a silly AdBlock rule
        return self.file_url.replace('media/ad', 'media/ax')

    # set by configure_libweasyl
    _base_file_path = None

    @property
    def full_file_path(self):
        return os.path.join(self._base_file_path, self.file_path)

    def serialize(self, recursive=1, link=None):
        ret = super(DiskMediaItem, self).serialize(recursive=recursive, link=link)
        ret['full_file_path'] = self.full_file_path
        return ret

    def as_image(self):
        return images.read(self.full_file_path.encode())


def fetch_or_create_media_item(*a, **kw):
    return DiskMediaItem.fetch_or_create(*a, **kw)


class _LinkMixin(object):
    cache_func = None
    _linkjoin = ()
    _load = ()

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
            cls.dbsession.query(MediaItem, cls)
            .with_polymorphic([DiskMediaItem])
            .join(cls, *cls._linkjoin)
            .options(joinedload('described'))
            .options(joinedload(cls._linkname))
            .filter(getattr(cls, cls._identity).in_(identities)))

        for load in cls._load:
            q = q.options(joinedload(load))

        buckets = collections.defaultdict(lambda: collections.defaultdict(list))
        for media_item, link in q.all():
            media_data = media_item.serialize(link=link)
            buckets[getattr(link, cls._identity)][link.link_type].append(media_data)
        return [dict(buckets[identity]) for identity in identities]

    @classmethod
    def register_cache(cls, func):
        cls.cache_func = staticmethod(func)
        return func


class SubmissionMediaLink(Base, _LinkMixin):
    __table__ = tables.submission_media_links

    _identity = 'submitid'
    _linkname = 'submission_links'
    _load = ('submission_links.submission', 'submission_links.submission.owner')

    submission = relationship(Submission, backref='media_links')
    media_item = relationship(MediaItem, backref='submission_links')


class UserMediaLink(Base, _LinkMixin):
    __table__ = tables.user_media_links

    _identity = 'userid'
    _linkname = 'user_links'

    user = relationship(
        Profile, backref='media_links',
        primaryjoin=foreign(__table__.c.userid) == remote(Profile.userid))
    media_item = relationship(MediaItem, backref='user_links')


class MediaMediaLink(Base, _LinkMixin):
    __table__ = tables.media_media_links

    _identity = 'describee_id'
    _linkname = 'describing'
    _linkjoin = __table__.c.described_with_id == MediaItem.mediaid,

    describee = relationship(
        MediaItem, backref='described',
        primaryjoin=foreign(__table__.c.describee_id) == remote(MediaItem.mediaid))
    media_item = relationship(
        MediaItem, backref='describing',
        primaryjoin=foreign(__table__.c.described_with_id) == remote(MediaItem.mediaid))

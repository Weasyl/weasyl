import hashlib
from io import BytesIO
import os

from sqlalchemy.orm import relationship, foreign, remote, joinedload, lazyload, load_only
from sqlalchemy.sql.expression import any_

from libweasyl.files import fanout
from libweasyl.models.meta import Base
from libweasyl.models.users import Profile
from libweasyl.models import tables
from libweasyl import flash, images


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

            # Write our file to disk
            real_path = obj.full_file_path
            os.makedirs(os.path.dirname(real_path), exist_ok=True)
            with open(real_path, 'wb') as outfile:
                outfile.write(data)

            cls.dbsession.add(obj)
        return obj

    # set by configure_libweasyl
    _media_link_formatter_callback = None
    _base_file_path = None

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
    def _file_path_components(self):
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

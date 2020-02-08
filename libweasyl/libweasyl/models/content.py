from __future__ import division

import warnings

import arrow
from pyramid.decorator import reify
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship
import sqlalchemy as sa

from libweasyl.constants import Category, DEFAULT_LIMITS, MEBIBYTE
from libweasyl.exceptions import InvalidData, RatingExceeded, SubmissionFileTooLarge
from libweasyl.files import file_type_for_category
from libweasyl.models.helpers import CharSettings, apply_validators, clauses_for, validator
from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables
from libweasyl.text import slug_for


class Tag(Base):
    __table__ = tables.searchtag

    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<Tag %r>' % (self.title,)


class SubmissionTag(Base):
    __table__ = tables.searchmapsubmit

    tag_object = relationship(Tag, uselist=False, lazy='joined')
    tag = association_proxy('tag_object', 'title')

    with clauses_for(__table__) as c:
        is_artist_tag = c('artist-tag')

    def __repr__(self):
        return '<SubmissionTag %r -> %r (%r)>' % (self.targetid, self.tagid, self.settings)


class JournalTag(Base):
    __table__ = tables.searchmapjournal


class CharacterTag(Base):
    __table__ = tables.searchmapchar


@apply_validators
class Submission(Base):
    __table__ = tables.submission

    now = staticmethod(arrow.get)

    owner = relationship(Login, backref='submissions')
    tag_objects = relationship(Tag, secondary=SubmissionTag.__table__)
    tags = association_proxy('tag_objects', 'title')

    with clauses_for(__table__) as c:
        is_hidden = c('hidden')
        is_friends_only = c('friends-only')
        is_critique = c('critique')
        is_google_doc = c('embed-type', 'google-drive')
        is_other_embed = c('embed-type', 'other')

    def legacy_path(self, mod=False):
        """
        Create the weasyl-old relative URL for a submission.

        Parameters:
            mod (bool): Whether or not to suffix ``?anyway=true`` on the URL for
                moderators.

        Returns:
            The relative URL.
        """
        ret = '/submission/%d/%s' % (self.submitid, slug_for(self.title))
        if mod:
            ret += '?anyway=true'
        return ret

    @reify
    def media(self):
        from libweasyl.media import get_submission_media
        return get_submission_media(self.submitid)

    @reify
    def submission_media(self):
        ret = self.media.get('submission')
        if ret:
            return ret[0]
        return None

    @reify
    def cover_media(self):
        ret = self.media.get('cover')
        if not ret and self.submission_media:
            ret = self.submission_media['described'].get('cover')
        if ret:
            return ret[0]
        return None

    @validator()
    def validate_rating(self, value, old_value, initiator):
        if self.owner is None:
            # 6 determined experimentally from the current version of SQLAlchemy.
            warnings.warn(
                'tried to set the rating on a Submission without an owner',
                RuntimeWarning, stacklevel=6)
            return
        if not self.owner.is_permitted_rating(value):
            raise RatingExceeded(
                'The rating %s exceeds the rating limit allowed for %s.' % (
                    value.nice_name, self.owner.profile.username))

    def set_tags(self, new_tags, done_by_artist=False):
        new_tags = set(new_tags)
        current_tags = SubmissionTag.query.filter_by(targetid=self.submitid).all()
        current_tags_set = {t.tag for t in current_tags}
        tags_to_add = new_tags - current_tags_set
        tags_to_remove = current_tags_set - new_tags

        if tags_to_add:
            entered_tags = Tag.query.filter(Tag.title.in_(tags_to_add)).all()
        else:
            entered_tags = []
        entered_tags_set = {t.title for t in entered_tags}
        tag_ids_to_add = {t.tagid for t in entered_tags}
        tags_to_enter = tags_to_add - entered_tags_set

        if tags_to_enter:
            q = (
                Tag.__table__.insert()
                .values([{'title': t} for t in tags_to_enter])
                .returning(Tag.tagid))
            tag_ids_to_add.update(t for t, in self.dbsession.execute(q).fetchall())

        if tag_ids_to_add:
            settings = CharSettings(set(), {}, {})
            if done_by_artist:
                settings.mutable_settings.add('artist-tag')
            q = (
                SubmissionTag.__table__.insert()
                .values([{'targetid': self.submitid, 'tagid': t, 'settings': settings} for t in tag_ids_to_add]))
            self.dbsession.execute(q)

        if tags_to_remove:
            tag_ids_to_remove = {t.tagid for t in current_tags if t.tag in tags_to_remove}
            q = (
                SubmissionTag.__table__.delete()
                .where(SubmissionTag.targetid == self.submitid)
                .where(SubmissionTag.tagid.in_(tag_ids_to_remove)))
            self.dbsession.execute(q)

    @classmethod
    def create(cls, owner, title, rating, description, category, subtype, folder, tags, friends_only=False,
               critique_requested=False, submission_data=None, embed_link=None, submission_size_limit=None):
        from libweasyl.media import fetch_or_create_media_item
        from libweasyl.models.media import SubmissionMediaLink

        now = cls.now()
        inst = cls(owner=owner, title=title, content=description, subtype=subtype, folder=folder, settings=None,
                   unixtime=now, sorttime=now)
        # must be set after 'owner' for validation.
        inst.rating = rating
        inst.is_friends_only = friends_only
        inst.is_critique = critique_requested

        submission_media_item = cover_media_item = thumbnail_media_item = None
        if embed_link is None:
            if submission_data is None:
                raise InvalidData("A submission file or an embed link is required.")
            submission_decoded, submission_format = file_type_for_category(submission_data, category)
            if submission_size_limit is None:
                submission_size_limit = DEFAULT_LIMITS[submission_format]
            if len(submission_data) > submission_size_limit:
                raise SubmissionFileTooLarge(
                    "The submission file uploaded exceeds the limit of %g mebibytes." % (
                        submission_size_limit / MEBIBYTE))
            submission_image = None
            if category == Category.visual:
                submission_image = submission_decoded
            submission_media_item = fetch_or_create_media_item(
                submission_data, file_type=submission_format, im=submission_image)
        elif category == Category.visual:
            raise ValueError('embedded visual submissions are not supported')
        elif submission_data is not None:
            raise InvalidData("You may not submit both submission data and an embed link.")
        elif category == Category.literary:
            inst.is_google_doc = True
            inst.google_doc = GoogleDocEmbed(embed_url=embed_link)
        elif category == Category.multimedia:
            inst.is_other_embed = True
            inst.content = '%s\n%s' % (embed_link, inst.content)
        else:
            raise ValueError('unknown submission category', category)

        if category == Category.visual:
            cover_media_item = submission_media_item.ensure_cover_image(submission_image)
            thumbnail_media_item = submission_media_item.make_thumbnail(submission_image)

        cls.dbsession.add(inst)
        cls.dbsession.flush()

        # The submission is in the database now, so tags and media links can be set.
        inst.set_tags(tags, done_by_artist=True)

        if submission_media_item is not None:
            SubmissionMediaLink.make_or_replace_link(inst.submitid, 'submission', submission_media_item)
        if cover_media_item is not None:
            SubmissionMediaLink.make_or_replace_link(inst.submitid, 'cover', cover_media_item)
        if thumbnail_media_item is not None:
            SubmissionMediaLink.make_or_replace_link(inst.submitid, 'thumbnail', thumbnail_media_item)

        return inst


class GoogleDocEmbed(Base):
    __table__ = tables.google_doc_embeds

    submission = relationship(Submission, backref=backref('google_doc', uselist=False))


class Comment(Base):
    __table__ = tables.comments

    _target_user = relationship(Login, foreign_keys=[__table__.c.target_user], backref='shouts')
    _target_sub = relationship(Submission, backref='comments')
    poster = relationship(Login, foreign_keys=[__table__.c.userid])

    @property
    def target(self):
        if self.target_user:
            return self._target_user
        elif self.target_sub:
            return self._target_sub
        else:
            raise ValueError('no target user or submission')


class Folder(Base):
    __table__ = tables.folder

    owner = relationship(Login, backref='folders')
    submissions = relationship(Submission, backref=backref('folder', uselist=False))

    with clauses_for(__table__) as c:
        is_featured = c('featured-filter')


class Journal(Base):
    __table__ = tables.journal

    owner = relationship(Login, backref='journals')

    with clauses_for(__table__) as c:
        is_hidden = c('hidden')

    def legacy_path(self, mod=False):
        """
        Create the weasyl-old relative URL for a journal.

        Parameters:
            mod (bool): Whether or not to suffix ``?anyway=true`` on the URL for
                moderators.

        Returns:
            The relative URL.
        """
        ret = '/journal/%d/%s' % (self.journalid, slug_for(self.title))
        if mod:
            ret += '?anyway=true'
        return ret


class JournalComment(Base):
    __table__ = tables.journalcomment


class Character(Base):
    __table__ = tables.character

    owner = relationship(Login, backref='characters')

    with clauses_for(__table__) as c:
        is_hidden = c('hidden')

    @property
    def title(self):
        return self.char_name

    def legacy_path(self, mod=False):
        """
        Create the weasyl-old relative URL for a character.

        Parameters:
            mod (bool): Whether or not to suffix ``?anyway=true`` on the URL for
                moderators.

        Returns:
            The relative URL.
        """
        ret = '/character/%d/%s' % (self.charid, slug_for(self.char_name))
        if mod:
            ret += '?anyway=true'
        return ret


class CharacterComment(Base):
    __table__ = tables.charcomment


class Blocktag(Base):
    __table__ = tables.blocktag

    @classmethod
    def blocked_tags(cls, userid, rating):
        return (
            sa.select([cls.tagid])
            .where(cls.userid == userid)
            .where(cls.rating <= rating))


class Favorite(Base):
    __table__ = tables.favorite


class ReportComment(Base):
    __table__ = tables.reportcomment

    poster = relationship(Login, backref='report_comments')


class Report(Base):
    __table__ = tables.report

    with clauses_for(__table__) as c:
        is_under_review = c('under-review')

    _target_user = relationship(Login, foreign_keys=[__table__.c.target_user], backref='profile_reports')
    _target_sub = relationship(Submission, backref='reports')
    _target_char = relationship(Character, backref='reports')
    _target_journal = relationship(Journal, backref='reports')
    _target_comment = relationship(Comment, backref='reports')
    comments = relationship(ReportComment, backref=backref('report', uselist=False))
    owner = relationship(Login, foreign_keys=[__table__.c.closerid], backref='owned_reports')

    @property
    def target(self):
        if self.target_user:
            return self._target_user
        elif self.target_sub:
            return self._target_sub
        elif self.target_char:
            return self._target_char
        elif self.target_journal:
            return self._target_journal
        elif self.target_comment:
            return self._target_comment
        else:
            raise ValueError('no target profile, user, character, journal, or comment')

    @property
    def target_type(self):
        if self.target_user:
            return 'profile'
        elif self.target_sub:
            return 'submission'
        elif self.target_char:
            return 'character'
        elif self.target_journal:
            return 'journal'
        elif self.target_comment:
            return 'comment'
        else:
            raise ValueError('no target profile, user, character, journal, or comment')

    @property
    def status(self):
        if self.closerid is None:
            return 'open'
        elif self.is_under_review:
            return 'review'
        else:
            return 'closed'

    @hybrid_property
    def is_closed(self):
        return self.closerid is not None and not self.is_under_review

    @is_closed.expression
    def is_closed(cls):
        return (None != cls.closerid) & (~cls.is_under_review)

    def related_reports(self):
        cls = type(self)
        q = (
            cls.query
            .filter_by(target_user=self.target_user, target_sub=self.target_sub,
                       target_char=self.target_char, target_journal=self.target_journal,
                       target_comment=self.target_comment)
            .filter(cls.reportid != self.reportid)
            .order_by(cls.opened_at.asc()))
        return q.all()

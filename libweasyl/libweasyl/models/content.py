from __future__ import division

from pyramid.decorator import reify
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship
import sqlalchemy as sa

from libweasyl.media import get_submission_media
from libweasyl.models.helpers import clauses_for
from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables
from libweasyl.text import slug_for


class Submission(Base):
    __table__ = tables.submission

    owner = relationship(Login)

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
        # TODO: this should be unnecessary
        if not ret and self.submission_media:
            ret = self.submission_media['described'].get('cover')
        if ret:
            return ret[0]
        return None


class Comment(Base):
    __table__ = tables.comments

    _target_user = relationship(Login, foreign_keys=[__table__.c.target_user])
    _target_sub = relationship(Submission)
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

    owner = relationship(Login)
    submissions = relationship(Submission, backref=backref('folder', uselist=False))

    with clauses_for(__table__) as c:
        is_featured = c('featured-filter')


class Journal(Base):
    __table__ = tables.journal

    owner = relationship(Login)

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

    owner = relationship(Login)

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

    poster = relationship(Login)


class Report(Base):
    __table__ = tables.report

    with clauses_for(__table__) as c:
        is_under_review = c('under-review')

    _target_user = relationship(Login, foreign_keys=[__table__.c.target_user])
    _target_sub = relationship(Submission)
    _target_char = relationship(Character)
    _target_journal = relationship(Journal)
    _target_comment = relationship(Comment)
    comments = relationship(ReportComment, backref=backref('report', uselist=False))
    owner = relationship(Login, foreign_keys=[__table__.c.closerid])

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

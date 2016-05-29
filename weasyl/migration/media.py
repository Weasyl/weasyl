import itertools
import sys

from sqlalchemy.orm import joinedload
import sqlalchemy as sa

from libweasyl import ratings

from weasyl.define import connect, meta
from weasyl import orm


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def batch_submissions(db, min_submission):
    q = db.query(orm.Submission).options(joinedload('login'))
    (max_id,), = db.execute(sa.select([sa.func.max(meta.tables['submission'].c.submitid)]))
    for min_id in xrange(min_submission, max_id + 1, 1000):
        yield min_id, q.filter((orm.Submission.submitid >= min_id) & (orm.Submission.submitid < min_id + 1000)).all()
    print 'last id:', max_id


def port_submissions(db, min_submission):
    for min_id, batch in batch_submissions(db, min_submission):
        print 'starting batch', min_id
        for submission in filter(None, batch):
            sml = cml = None

            if 'submit' in submission.settings.file_types and 'gdocs-embed' not in submission.settings:
                sml = orm.SubmissionMediaLink(
                    submission=submission,
                    media_item=orm.DiskMediaItem(
                        attributes={},
                        file_type=submission.settings.file_types['submit'],
                        file_path=submission.legacy_submission_path(),
                        file_url='/' + submission.legacy_submission_path(with_login_name=True),
                    ),
                    link_type='submission',
                    attributes={'rating': submission.rating},
                )
                db.add(sml)

            if 'thumb' in submission.settings.file_types:
                db.add(orm.SubmissionMediaLink(
                    submission=submission,
                    media_item=orm.DiskMediaItem(
                        attributes={},
                        file_type=submission.settings.file_types['thumb'],
                        file_path=submission.legacy_thumbnail_path(),
                        file_url='/' + submission.legacy_thumbnail_path(),
                    ),
                    link_type='thumbnail',
                    attributes={'rating': submission.rating},
                ))

            if 'cover' in submission.settings.file_types:
                cml = orm.SubmissionMediaLink(
                    submission=submission,
                    media_item=orm.DiskMediaItem(
                        attributes={},
                        file_type=submission.settings.file_types['cover'],
                        file_path=submission.legacy_cover_path(),
                        file_url='/' + submission.legacy_cover_path(),
                    ),
                    link_type='cover',
                    attributes={'rating': submission.rating},
                )
                db.add(cml)

            if sml is not None and cml is not None and sml.media_item.file_type in ('jpg', 'png', 'gif'):
                db.add(orm.MediaMediaLink(
                    describee=sml.media_item,
                    media_item=cml.media_item,
                    link_type='cover',
                    attributes={},
                ))

        db.flush()
        print 'inserted'


def batch_users(db):
    q = db.query(orm.Profile)
    (max_id,), = db.execute(sa.select([sa.func.max(meta.tables['profile'].c.userid)]))
    for min_id in xrange(0, max_id, 1000):
        yield min_id, q.filter((orm.Profile.userid >= min_id) & (orm.Profile.userid < min_id + 1000)).all()


def port_users(db):
    for min_id, batch in batch_users(db):
        print 'starting batch', min_id
        for user in filter(None, batch):
            if 'banner' in user.config.file_types:
                db.add(orm.UserMediaLink(
                    user=user,
                    media_item=orm.DiskMediaItem(
                        attributes={},
                        file_type=user.config.file_types['banner'],
                        file_path=user.legacy_banner_path(),
                        file_url='/' + user.legacy_banner_path(),
                    ),
                    link_type='banner',
                    attributes={'rating': ratings.GENERAL.code},
                ))

            if 'avatar' in user.config.file_types:
                db.add(orm.UserMediaLink(
                    user=user,
                    media_item=orm.DiskMediaItem(
                        attributes={},
                        file_type=user.config.file_types['avatar'],
                        file_path=user.legacy_avatar_path(),
                        file_url='/' + user.legacy_avatar_path(),
                    ),
                    link_type='avatar',
                    attributes={'rating': ratings.GENERAL.code},
                ))

        db.flush()
        print 'inserted'


def main():
    do_users, min_submission = sys.argv[1:]
    db = connect()
    if do_users == 'yes':
        print 'starting users'
        port_users(db)
    print 'starting submissions'
    port_submissions(db, int(min_submission))


if __name__ == '__main__':
    main()

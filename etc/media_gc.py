import errno
import os
import sys

import sqlalchemy as sa

from weasyl import orm, define


def main():
    db = define.connect()
    all_media = sa.union(
        sa.select([orm.UserMediaLink.mediaid]),
        sa.select([orm.SubmissionMediaLink.mediaid]),
        sa.select([orm.MediaMediaLink.describee_id]),
        sa.select([orm.MediaMediaLink.described_with_id]),
    ).alias('all_media')
    q = (
        db.query(orm.MediaItem)
        .with_polymorphic([orm.DiskMediaItem])
        .outerjoin(all_media)
        .filter(all_media.c.mediaid == None))
    count = q.count()
    for e, media_item in enumerate(q, start=1):
        sys.stdout.write('\r%d/%d' % (e, count))
        sys.stdout.flush()
        db.delete(media_item)
        try:
            os.unlink(media_item.full_file_path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                continue
            raise
    db.flush()
    print


if __name__ == '__main__':
    main()

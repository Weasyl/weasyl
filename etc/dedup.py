import sys

import sqlalchemy as sa

from weasyl import define as d
from weasyl import orm


def main():
    db = d.connect()
    q = (
        sa.select([sa.func.array_agg(orm.MediaItem.mediaid)])
        .where(orm.MediaItem.sha256 != None)
        .group_by(orm.MediaItem.sha256)
        .having(sa.func.count() > 1))
    [[count]] = db.execute(
        sa.select([sa.func.count()])
        .select_from(q.alias('query'))
    ).fetchall()
    for e, (mediaids,) in enumerate(db.execute(q), start=1):
        sys.stdout.write('\r%d/%d' % (e, count))
        sys.stdout.flush()
        old_media_item = db.query(orm.DiskMediaItem).get(mediaids[0])
        new_media_item = orm.DiskMediaItem(
            sha256=old_media_item.sha256, file_type=old_media_item.file_type)
        with open(old_media_item.full_file_path, 'rb') as infile:
            data = infile.read()
        new_media_item.init_from_data(data)
        db.add(new_media_item)
        db.flush()
        for table, column in [('submission_media_links', 'mediaid'),
                              ('user_media_links', 'mediaid'),
                              ('media_media_links', 'described_with_id'),
                              ('media_media_links', 'describee_id')]:
            table_obj = d.meta.tables[table]
            q = (
                table_obj.update()
                .values(**{column: new_media_item.mediaid})
                .where(table_obj.c[column].in_(mediaids)))
            db.execute(q)
    print


if __name__ == '__main__':
    main()

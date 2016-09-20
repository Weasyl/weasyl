import errno
import hashlib

import sqlalchemy as sa

from weasyl.define import meta, sessionmaker
from weasyl import orm


def batch_media_items(db):
    q = (db.query(orm.MediaItem)
         .with_polymorphic(orm.DiskMediaItem)
         .filter(orm.MediaItem.sha256 == None))
    (max_id,), = db.execute(sa.select([sa.func.max(meta.tables['media'].c.mediaid)]))
    for min_id in xrange(0, max_id + 1, 1000):
        yield min_id, q.filter((orm.MediaItem.mediaid >= min_id) & (orm.MediaItem.mediaid < min_id + 1000)).all()
    print 'last id:', max_id


def port_media_items(db):
    for min_id, batch in batch_media_items(db):
        print 'starting batch', min_id
        for media_item in filter(None, batch):
            try:
                infile = open(media_item.full_file_path, 'rb')
            except IOError as e:
                if e.errno == errno.ENOENT:
                    continue
                raise
            with infile:
                hash_obj = hashlib.sha256()
                for chunk in iter(lambda: infile.read(4096), ''):
                    hash_obj.update(chunk)
                media_item.sha256 = hash_obj.hexdigest()

        db.flush()
        print 'inserted'


def main():
    db = sessionmaker()
    print 'starting media_items'
    port_media_items(db)


if __name__ == '__main__':
    main()

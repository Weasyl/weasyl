import errno
import sys

from weasyl import orm, define


def main():
    db = define.connect()
    q = (
        db.query(orm.MediaItem.mediaid)
        .filter(orm.MediaItem.sha256 != None)
        .filter(orm.MediaItem.file_type.in_(['jpg', 'png', 'gif']))
        .order_by(orm.MediaItem.sha256.asc()))
    count = q.count()
    for e, (mediaid,) in enumerate(q, start=1):
        sys.stdout.write('\r%d/%d' % (e, count))
        sys.stdout.flush()
        m = db.query(orm.DiskMediaItem).get(mediaid)
        try:
            im = m.as_image()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            print "\rcouldn't locate", m.mediaid
        else:
            m.attributes.update({'width': im.size.width, 'height': im.size.height})
            m.attributes.changed()
            db.flush()
    print


if __name__ == '__main__':
    main()

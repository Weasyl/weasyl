import errno
import sys

from libweasyl import flash
from weasyl import orm, define
# This import is required because it configures libweasyl.
import weasyl.wsgi


_shush_pyflakes = [weasyl.wsgi]


def main():
    db = define.connect()
    q = (
        db.query(orm.MediaItem.mediaid)
        .filter(orm.MediaItem.sha256 != None)
        .filter(orm.MediaItem.file_type == 'swf')
        .order_by(orm.MediaItem.sha256.asc()))
    count = q.count()
    for e, (mediaid,) in enumerate(q, start=1):
        sys.stderr.write('\r%d/%d' % (e, count))
        m = db.query(orm.DiskMediaItem).get(mediaid)
        try:
            infile = open(m.full_file_path, 'rb')
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            print "\rcouldn't locate", m.mediaid
        else:
            with infile:
                m.attributes.update(flash.parse_flash_header(infile))
            m.attributes.changed()
            db.flush()
    print


if __name__ == '__main__':
    main()

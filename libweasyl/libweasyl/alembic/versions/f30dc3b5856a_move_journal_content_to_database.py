# encoding: utf-8

"""Move journal content to database

Revision ID: f30dc3b5856a
Revises: 088e13f2ae70
Create Date: 2017-08-21 07:33:55.535625

"""

# revision identifiers, used by Alembic.
revision = 'f30dc3b5856a'
down_revision = '088e13f2ae70'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]

import codecs
import errno
import hashlib
import os


def _get_hash_path(journal_root, journal_id):
    id_hash = hashlib.sha1(str(journal_id)).hexdigest()
    hash_path = tuple(id_hash[i:i + 2] for i in range(0, 11, 2)) + ('%d.txt' % (journal_id,),)

    return os.path.join(journal_root, *hash_path)


def _try_read(paths):
    for p in paths:
        try:
            with codecs.open(p, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    return None


def upgrade():
    journal_root = os.path.join(os.environ['WEASYL_STORAGE_ROOT'], 'static/journal')

    connection = op.get_bind()

    query = connection.execute("SELECT journalid, position('h' in settings) != 0 FROM journal WHERE content IS NULL")
    updates = []

    for journal_id, is_hidden in query:
        content = _try_read([
            os.path.join(journal_root, '%d.txt' % (journal_id,)),
            _get_hash_path(journal_root, journal_id),
        ])

        if content is not None:
            updates.append((journal_id, content))
        elif not is_hidden:
            # Python 2 doesn’t have FileNotFoundError
            raise IOError("Missing journal file for non-hidden journal %d; hide journals with known missing files before running this migration" % (journal_id,))

    if updates:
        connection.execute(
            """
            UPDATE journal
                SET content = t.content
                FROM UNNEST (%(updates)s) AS t (journalid integer, content unknown)
                WHERE
                    journal.journalid = t.journalid AND
                    journal.content IS NULL
            """,
            updates=updates,
        )

    connection.execute("UPDATE journal SET content = '(file missing)' WHERE content IS NULL AND position('h' in settings) != 0")

    op.alter_column('journal', 'content',
               existing_type=sa.TEXT(),
               nullable=False)


def downgrade():
    op.alter_column('journal', 'content',
               existing_type=sa.TEXT(),
               nullable=True)

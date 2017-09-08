"""Move journal content to database

Revision ID: f30dc3b5856a
Revises: 088e13f2ae70
Create Date: 2017-08-21 07:33:55.535625

"""

# revision identifiers, used by Alembic.
revision = 'f30dc3b5856a'
down_revision = '088e13f2ae70'

from alembic import op
import sqlalchemy as sa

import codecs
import errno
import hashlib
import os


def _get_hash_path(journal_id):
    journal_root = os.path.join(os.environ['WEASYL_ROOT'], 'static/journal')
    id_hash = hashlib.sha1(str(journal_id)).hexdigest()
    hash_path = tuple(id_hash[i:i + 2] for i in range(0, 11, 2)) + ('%d.txt' % (journal_id,),)

    return os.path.join(journal_root, *hash_path)


def upgrade():
    connection = op.get_bind()

    query = connection.execute("SELECT journalid, position('h' in settings) != 0 FROM journal WHERE content IS NULL")
    updates = []

    for journal_id, is_hidden in query:
        try:
            with codecs.open(_get_hash_path(journal_id), 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except IOError as e:
            if e.errno != errno.ENOENT or not is_hidden:
                raise
        else:
            updates.append((journal_id, content))

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

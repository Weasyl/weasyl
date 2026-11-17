"""frienduser constraints

Revision ID: 6421032c567d
Revises: abac1922735d
Create Date: 2026-01-07 08:13:58.378755

"""

# revision identifiers, used by Alembic.
revision = '6421032c567d'
down_revision = 'abac1922735d'

import sqlalchemy as sa
from alembic import op
from psycopg2.errors import DuplicateObject


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_frienduser_userid")

        try:
            op.execute("ALTER TABLE frienduser ADD CONSTRAINT frienduser_settings_check CHECK (settings IN ('', 'p')) NOT VALID")
        except sa.exc.ProgrammingError as e:
            if not isinstance(e.orig, DuplicateObject):
                raise

        op.execute("ALTER TABLE frienduser VALIDATE CONSTRAINT frienduser_settings_check")

        op.execute(
            "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS ind_frienduser_uniq"
            " ON frienduser (least(userid, otherid), (userid # otherid))"
        )


def downgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_frienduser_uniq")
        op.execute("ALTER TABLE frienduser DROP CONSTRAINT IF EXISTS frienduser_settings_check")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_frienduser_userid ON frienduser (userid)")

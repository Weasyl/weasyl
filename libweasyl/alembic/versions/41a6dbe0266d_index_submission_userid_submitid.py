"""Index submission (userid, submitid)

Revision ID: 41a6dbe0266d
Revises: 89ee13bfd34f
Create Date: 2021-07-19 06:15:54.003793

"""

# revision identifiers, used by Alembic.
revision = '41a6dbe0266d'
down_revision = '89ee13bfd34f'

from alembic import op


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_userid_submitid ON submission (userid, submitid)")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_userid")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_userid_folderid_submitid ON submission (userid, folderid, submitid) WHERE folderid IS NOT NULL")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_userid_folderid")


def downgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_userid ON submission (userid)")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_userid_submitid")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_userid_folderid ON submission (userid, folderid)")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_userid_folderid_submitid")

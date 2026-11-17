"""Remove outdated index condition

Revision ID: bcb0d75b6f8b
Revises: 41a6dbe0266d
Create Date: 2021-07-22 01:26:20.485966

"""

# revision identifiers, used by Alembic.
revision = 'bcb0d75b6f8b'
down_revision = '41a6dbe0266d'

from alembic import op


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_score_new ON submission (
                (
                    log(favorites + 1)
                        + log(page_views + 1) / 2
                        + unixtime / 180000.0
                )
            )
        """)
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_score")
        op.execute("ALTER INDEX ind_submission_score_new RENAME TO ind_submission_score")


def downgrade():
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_score_old ON submission (
                (
                    log(favorites + 1)
                        + log(page_views + 1) / 2
                        + unixtime / 180000.0
                )
            ) WHERE favorites IS NOT NULL
        """)
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_score")
        op.execute("ALTER INDEX ind_submission_score_old RENAME TO ind_submission_score")

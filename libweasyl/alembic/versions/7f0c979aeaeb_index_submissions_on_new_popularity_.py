"""Index submissions on new popularity score

Revision ID: 7f0c979aeaeb
Revises: 63baa2713e72
Create Date: 2024-08-15 02:45:29.390391

"""

# revision identifiers, used by Alembic.
revision = '7f0c979aeaeb'
down_revision = '63baa2713e72'

from alembic import op


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_submission_score2 ON submission (
                (
                    log(favorites)
                        + unixtime / 180000.0
                )
            ) WHERE favorites > 0
        """)


def downgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_submission_score2")

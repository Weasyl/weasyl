"""Add index on submission popularity score

Revision ID: 8e98a1be126e
Revises: dde33da7c33c
Create Date: 2019-10-24 17:06:22.092041

"""

# revision identifiers, used by Alembic.
revision = '8e98a1be126e'
down_revision = 'dde33da7c33c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(
        'ind_submission_score',
        'submission',
        [
            sa.text("""(
                log(favorites + 1)
                    + log(page_views + 1) / 2
                    + unixtime / 180000.0
            )"""),
        ],
        unique=False,
        postgresql_where=sa.text("favorites IS NOT NULL"),
    )


def downgrade():
    op.drop_index('ind_submission_score', table_name='submission')

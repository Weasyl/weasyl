"""Fill in favorite count for submissions

Revision ID: 5a6d74c75fa6
Revises: 4b6fd0d48a2b
Create Date: 2020-02-25 09:11:34.348670

"""

# revision identifiers, used by Alembic.
revision = '5a6d74c75fa6'
down_revision = '4b6fd0d48a2b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute(
        "UPDATE submission"
        " SET favorites = f.count"
        " FROM (SELECT targetid, count(*) FROM favorite WHERE type = 's' GROUP BY targetid) f"
        " WHERE f.targetid = submission.submitid"
        " AND submission.favorites IS NULL"
    )

    op.execute(
        "UPDATE submission"
        " SET favorites = 0"
        " WHERE favorites IS NULL"
    )

    op.alter_column('submission', 'favorites',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade():
    op.alter_column('submission', 'favorites',
               existing_type=sa.INTEGER(),
               nullable=True)

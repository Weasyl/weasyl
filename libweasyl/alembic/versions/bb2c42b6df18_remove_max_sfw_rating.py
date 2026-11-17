"""Remove max_sfw_rating

Revision ID: bb2c42b6df18
Revises: 63baa2713e72
Create Date: 2025-06-09 03:43:50.460340

"""

# revision identifiers, used by Alembic.
revision = 'bb2c42b6df18'
down_revision = '63baa2713e72'

from alembic import op


def upgrade():
    op.execute("UPDATE profile SET jsonb_settings = jsonb_settings - 'max_sfw_rating'")


def downgrade():
    # irreversible!
    pass

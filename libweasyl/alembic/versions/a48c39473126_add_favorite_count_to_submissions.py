"""Add favorite count to submissions

Revision ID: a48c39473126
Revises: 9270baf773a5
Create Date: 2019-09-06 02:10:37.903497

"""

# revision identifiers, used by Alembic.
revision = 'a48c39473126'
down_revision = '9270baf773a5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('submission', sa.Column('favorites', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('submission', 'favorites')

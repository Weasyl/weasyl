"""Do not index favorites by unixtime

Revision ID: 48ab4dc5599f
Revises: d0bffaa55b06
Create Date: 2016-07-05 21:37:22.666480

"""

# revision identifiers, used by Alembic.
revision = '48ab4dc5599f'
down_revision = 'd0bffaa55b06'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index('ind_favorite_unixtime', table_name='favorite')


def downgrade():
    op.create_index('ind_favorite_unixtime', 'favorite', ['unixtime'], unique=False)

"""Index favorites by unixtime

Revision ID: d0bffaa55b06
Revises: 9afc9a45510c
Create Date: 2016-06-17 20:17:14.270674

"""

# revision identifiers, used by Alembic.
revision = 'd0bffaa55b06'
down_revision = '9afc9a45510c'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.create_index('ind_favorite_unixtime', 'favorite', ['unixtime'], unique=False)


def downgrade():
    op.drop_index('ind_favorite_unixtime', table_name='favorite')

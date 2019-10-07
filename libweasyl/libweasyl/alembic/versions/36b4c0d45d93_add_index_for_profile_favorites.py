"""Add index for profile favorites

Revision ID: 36b4c0d45d93
Revises: b194ab27295e
Create Date: 2018-07-08 18:10:43.095681

"""

# revision identifiers, used by Alembic.
revision = '36b4c0d45d93'
down_revision = 'b194ab27295e'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.create_index('ind_favorite_userid_type_unixtime', 'favorite', ['userid', 'type', 'unixtime'], unique=False)


def downgrade():
    op.drop_index('ind_favorite_userid_type_unixtime', table_name='favorite')

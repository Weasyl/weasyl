"""Convert timestamp on collection table to Datetime

Revision ID: 3618355655c2
Revises: 1307b62614a4
Create Date: 2020-02-27 14:48:45.657000

"""

# revision identifiers, used by Alembic.
revision = '3618355655c2'
down_revision = '1307b62614a4'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('collection', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='timestamp')


def downgrade():
    pass


"""Convert message timestamps to Datetime

Revision ID: 096beed48d55
Revises: 662f0e636c29
Create Date: 2020-02-27 17:45:50.798000

"""

# revision identifiers, used by Alembic.
revision = '096beed48d55'
down_revision = '662f0e636c29'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('message', 'unixtime',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               server_default=sa.text(u'now()'),
               new_column_name="timestamp",
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';")


def downgrade():
    op.alter_column('message', 'timestamp',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.INTEGER(),
               existing_nullable=False,
               new_column_name="unixtime")
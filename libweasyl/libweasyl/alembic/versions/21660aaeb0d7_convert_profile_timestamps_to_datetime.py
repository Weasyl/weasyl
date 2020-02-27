"""Convert profile timestamps to Datetime

Revision ID: 21660aaeb0d7
Revises: 096beed48d55
Create Date: 2020-02-27 18:02:57.260000

"""

# revision identifiers, used by Alembic.
revision = '21660aaeb0d7'
down_revision = '096beed48d55'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('profile', 'unixtime',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               server_default=sa.text(u'now()'),
               new_column_name="timestamp",
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';")


def downgrade():
    pass

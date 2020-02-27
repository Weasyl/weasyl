"""Convert reportcomment timestamps to Datetime

Revision ID: 067398314d4e
Revises: 21660aaeb0d7
Create Date: 2020-02-27 18:41:21.478000

"""

# revision identifiers, used by Alembic.
revision = '067398314d4e'
down_revision = '21660aaeb0d7'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('reportcomment', 'unixtime',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               server_default=sa.text(u'now()'),
               new_column_name="timestamp",
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';")


def downgrade():
    pass


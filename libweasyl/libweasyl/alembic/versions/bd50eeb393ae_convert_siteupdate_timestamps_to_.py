"""Convert siteupdate timestamps to Datetime

Revision ID: bd50eeb393ae
Revises: 067398314d4e
Create Date: 2020-02-27 18:52:07.384000

"""

# revision identifiers, used by Alembic.
revision = 'bd50eeb393ae'
down_revision = '067398314d4e'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('siteupdate', 'unixtime',
               existing_type=sa.INTEGER(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               server_default=sa.text(u'now()'),
               new_column_name="timestamp",
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';")


def downgrade():
    pass

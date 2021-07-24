"""Convert profile timestamps to Datetime

Revision ID: 21660aaeb0d7
Revises: 096beed48d55
Create Date: 2020-02-27 18:02:57.260000

"""

# revision identifiers, used by Alembic.
revision = '21660aaeb0d7'
down_revision = 'e0320dc462db'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects.postgresql import TIMESTAMP

def upgrade():
    op.alter_column('profile', 'unixtime',
               existing_type=sa.INTEGER(),
               type_=TIMESTAMP(timezone=True),
               existing_nullable=False,
               server_default=sa.text(u'now()'),
               new_column_name="created_at",
               postgresql_using="to_timestamp(unixtime + 18000)")


def downgrade():
    op.alter_column('profile', 'created_at', server_default=None)
    op.alter_column('profile', 'created_at',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at) - 18000",
                    new_column_name='unixtime')

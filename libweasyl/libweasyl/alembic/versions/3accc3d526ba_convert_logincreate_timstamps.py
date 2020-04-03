"""Convert logincreate timestamps to TIMESTAMP(timzone=True)

Revision ID: 3accc3d526ba
Revises: 2e25bc9a0896
Create Date: 2020-02-27 16:06:48.018000

"""

# revision identifiers, used by Alembic.
revision = '3accc3d526ba'
down_revision = '2e25bc9a0896'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects.postgresql import TIMESTAMP


def upgrade():
    op.alter_column('logincreate', 'unixtime',
                    existing_type=sa.INTEGER(),
                    server_default=sa.func.now(),
                    type_=TIMESTAMP(timezone=True),
                    existing_nullable=False,
                    postgresql_using="to_timestamp(unixtime + 18000)",
                    new_column_name='created_at')


def downgrade():
    op.alter_column('logincreate', 'created_at', server_default=None)
    op.alter_column('logincreate', 'created_at',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at) - 18000",
                    new_column_name='unixtime')

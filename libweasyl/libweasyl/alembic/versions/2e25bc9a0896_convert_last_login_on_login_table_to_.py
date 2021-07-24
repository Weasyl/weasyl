"""Convert last_login on login  table to Datetime

Revision ID: 2e25bc9a0896
Revises: 3618355655c2
Create Date: 2020-02-27 15:02:32.668000

"""

# revision identifiers, used by Alembic.
revision = '2e25bc9a0896'
down_revision = '21660aaeb0d7'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects.postgresql import TIMESTAMP


def upgrade():
    op.alter_column('login', 'last_login',
               existing_type=sa.INTEGER(),
               type_=TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="to_timestamp(last_login + 18000)")


def downgrade():
    op.alter_column('login', 'last_login',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from last_login) - 18000")

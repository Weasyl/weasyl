"""Convert userinfo birthday to TIMESTAMP

Revision ID: 662f0e636c29
Revises: 3accc3d526ba
Create Date: 2020-02-27 17:01:16.591000

"""

# revision identifiers, used by Alembic.
revision = '662f0e636c29'
down_revision = '3accc3d526ba'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects.postgresql import TIMESTAMP


def upgrade():
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.INTEGER(),
               type_=TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="to_timestamp(birthday + 18000)")


def downgrade():
    op.alter_column('userinfo', 'birthday',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from birthday) - 18000")

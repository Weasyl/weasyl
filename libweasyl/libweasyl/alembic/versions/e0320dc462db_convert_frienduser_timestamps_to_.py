"""convert frienduser timestamps to DateTime

Revision ID: e0320dc462db
Revises: 1d8412df7346
Create Date: 2020-02-26 18:18:58.505000

"""

# revision identifiers, used by Alembic.
revision = 'e0320dc462db'
down_revision = 'cc2f96b0ba35'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects.postgresql import TIMESTAMP


def upgrade():
    op.alter_column('watchuser', 'unixtime', server_default=None)
    op.alter_column('watchuser', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="to_timestamp(unixtime + 18000)",
               new_column_name='created_at')
    op.alter_column('frienduser', 'unixtime', server_default=None)
    op.alter_column('frienduser', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=TIMESTAMP(timezone=True),
               existing_nullable=False,
               postgresql_using="to_timestamp(unixtime + 18000)",
               new_column_name='created_at')


def downgrade():
    op.alter_column('watchuser', 'created_at', server_default=None)
    op.alter_column('watchuser', 'created_at',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    server_default=sa.text(u"(date_part('epoch'::text, now()) - (18000)::double precision)"),
                    postgresql_using="extract(epoch from created_at) - 18000",
                    new_column_name='unixtime')
    op.alter_column('frienduser', 'created_at', server_default=None)
    op.alter_column('frienduser', 'created_at',
                    existing_type=TIMESTAMP(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    server_default=sa.text(u"(date_part('epoch'::text, now()) - (18000)::double precision)"),
                    postgresql_using="extract(epoch from created_at) - 18000",
                    new_column_name='unixtime')

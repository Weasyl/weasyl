"""convert character timestamps to DateTime

Revision ID: adca032b6782
Revises: e0320dc462db
Create Date: 2020-02-26 18:32:54.702000

"""

# revision identifiers, used by Alembic.
revision = 'adca032b6782'
down_revision = 'e0320dc462db'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('character', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='timestamp')


def downgrade():
    pass

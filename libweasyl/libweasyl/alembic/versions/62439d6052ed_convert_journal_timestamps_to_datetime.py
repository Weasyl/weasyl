"""convert journal timestamps to DateTime

Revision ID: 62439d6052ed
Revises: adca032b6782
Create Date: 2020-02-26 18:54:12.412000

"""

# revision identifiers, used by Alembic.
revision = '62439d6052ed'
down_revision = 'adca032b6782'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('journal', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='timestamp')


def downgrade():
    pass
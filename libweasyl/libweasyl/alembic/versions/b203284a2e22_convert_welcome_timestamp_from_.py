"""Convert welcome timestamp from WeasylTimestampColumn to DateTime(timezone=True)

Revision ID: b203284a2e22
Revises: 1dd77df0768f
Create Date: 2020-02-27 23:40:56.482000

"""

# revision identifiers, used by Alembic.
revision = 'b203284a2e22'
down_revision = '1dd77df0768f'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.drop_index('ind_welcome_unixtime', table_name='welcome')
    op.alter_column('welcome', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='timestamp')
    op.create_index('ind_welcome_timestamp', 'welcome', ['timestamp'], unique=False)


def downgrade():
    pass

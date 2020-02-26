"""convert and standerdize comment timestamps

Revision ID: b45d57142cb9
Revises: 4b6fd0d48a2b
Create Date: 2020-02-26 14:57:26.592000

"""

# revision identifiers, used by Alembic.
revision = 'b45d57142cb9'
down_revision = '4b6fd0d48a2b'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from sqlalchemy.dialects import postgresql


def upgrade():
    op.alter_column('charcomment', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='created_at')
    op.alter_column('comments', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='created_at')
    op.alter_column('journalcomment', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='created_at')
    op.alter_column('siteupdatecomment', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)


def downgrade():
    op.alter_column('charcomment', 'created_at', server_default=None)
    op.alter_column('charcomment', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at)+18000;",
                    new_column_name='unixtime')
    op.alter_column('comments', 'created_at', server_default=None)
    op.alter_column('comments', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at)+18000;",
                    new_column_name='unixtime')
    op.alter_column('journalcomment', 'created_at', server_default=None)
    op.alter_column('journalcomment', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at)+18000;",
                    new_column_name='unixtime')
    op.alter_column('siteupdatecomment', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    type_=postgresql.TIMESTAMP(timezone=True),
                    existing_nullable=False)

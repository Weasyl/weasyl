"""convert favorite timestamps to DateTime

Revision ID: 1d8412df7346
Revises: b45d57142cb9
Create Date: 2020-02-26 17:31:21.520000

"""

# revision identifiers, used by Alembic.
revision = '1d8412df7346'
down_revision = 'b45d57142cb9'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.drop_index('ind_favorite_userid_type_unixtime', table_name='favorite')
    op.alter_column('favorite', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='created_at')
    op.create_index('ind_favorite_userid_type_created_at', 'favorite', ['userid', 'type', 'created_at'], unique=False)


def downgrade():
    op.drop_index('ind_favorite_userid_type_created_at', table_name='favorite')
    op.alter_column('favorite', 'created_at', server_default=None)
    op.alter_column('favorite', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.INTEGER(),
                    existing_nullable=False,
                    postgresql_using="extract(epoch from created_at)+18000;",
                    new_column_name='unixtime')
    op.create_index('ind_favorite_userid_type_unixtime', 'favorite', ['userid', 'type', 'unixtime'], unique=False)

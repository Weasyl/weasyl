"""convert forgotpassword timestamps to DateTime

Revision ID: 75bf9a322d49
Revises: b203284a2e22
Create Date: 2020-02-28 15:59:57.414000

"""

# revision identifiers, used by Alembic.
revision = '75bf9a322d49'
down_revision = 'b203284a2e22'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.alter_column('forgotpassword', 'link_time', server_default=None)
    op.alter_column('forgotpassword', 'link_time',
               existing_type=sa.INTEGER(),
               server_default=sa.text(u"TIMESTAMP 'epoch'"),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (link_time-18000) * interval '1 second';"
               )
    op.alter_column('forgotpassword', 'set_time',
               existing_type=sa.INTEGER(),
               server_default=sa.text(u'now()'),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (set_time-18000) * interval '1 second';"
               )


def downgrade():
    pass


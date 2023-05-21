"""Index sorted inbox/outbox views

Revision ID: ed80016034fd
Revises: 259bc2d8e46c
Create Date: 2021-07-08 19:10:42.862537

"""

# revision identifiers, used by Alembic.
revision = 'ed80016034fd'
down_revision = '259bc2d8e46c'

from alembic import op


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_message_otherid_noteid ON message (otherid, noteid)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_message_userid_noteid ON message (userid, noteid)")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_message_otherid")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_message_userid")


def downgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_message_otherid ON message (otherid)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ind_message_userid ON message (userid)")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_message_otherid_noteid")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ind_message_userid_noteid")

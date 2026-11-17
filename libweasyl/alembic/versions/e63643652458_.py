"""Create per-user last read site update tracker

Revision ID: e63643652458
Revises: bb2c42b6df18
Create Date: 2025-07-17 03:12:45.791830

"""

# revision identifiers, used by Alembic.
revision = 'e63643652458'
down_revision = 'bb2c42b6df18'

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()

    op.add_column('login', sa.Column('last_read_updateid', sa.Integer(), nullable=True))
    op.create_foreign_key('login_last_read_updateid_fkey', 'login', 'siteupdate', ['last_read_updateid'], ['updateid'])

    # The last site update on production was from nearly four years ago.
    # Adjusting siteupdateread.updateid based on a user's unread site update
    # notifications in the welcome table is therefore not worth the effort.
    with context.autocommit_block():
        context.bind.execute('DELETE FROM welcome WHERE type = 3150')
        latest_updateid = context.bind.scalar(sa.text('SELECT MAX(updateid) FROM siteupdate'))
        context.bind.execute(sa.text('''
            UPDATE login
            SET last_read_updateid = :updateid
        '''), {'updateid': latest_updateid})


def downgrade():
    op.drop_constraint('login_last_read_updateid_fkey', 'login', type_='foreignkey')
    op.drop_column('login', 'last_read_updateid')

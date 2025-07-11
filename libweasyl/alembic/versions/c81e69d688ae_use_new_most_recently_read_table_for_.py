"""Use new most-recently-read table for site update notifications

Revision ID: c81e69d688ae
Revises: bb2c42b6df18
Create Date: 2025-07-11 01:22:50.032164

"""

# revision identifiers, used by Alembic.
revision = 'c81e69d688ae'
down_revision = 'bb2c42b6df18'

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()

    op.create_table('siteupdateread',
        sa.Column('readid', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.Column('updateid', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updateid'], ['siteupdate.updateid'], name='siteupdateread_updateid_fkey'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='siteupdateread_userid_fkey'),
        sa.PrimaryKeyConstraint('readid')
    )
    op.create_index('ind_siteupdateread_userid', 'siteupdateread', ['userid'], unique=False)

    # The last site update on production was from nearly four years ago.
    # Adjusting siteupdateread.updateid based on a user's unread site update
    # notifications in the welcome table is therefore not worth the effort.
    with context.autocommit_block():
        context.bind.execute('DELETE FROM welcome WHERE type = 3150')
        latest_updateid = context.bind.scalar(sa.text('SELECT MAX(updateid) FROM siteupdate'))
        context.bind.execute(sa.text('''
            INSERT INTO siteupdateread (userid, updateid)
            SELECT userid, :updateid
            FROM login
        '''), {'updateid': latest_updateid})


def downgrade():
    op.drop_index('ind_siteupdateread_userid', table_name='siteupdateread')
    op.drop_table('siteupdateread')

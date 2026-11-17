"""Remove unused welcomecount

Revision ID: 7a52ff794d57
Revises: 79ee87f22571
Create Date: 2023-01-03 08:11:07.992686

"""

# revision identifiers, used by Alembic.
revision = '7a52ff794d57'
down_revision = '79ee87f22571'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('welcomecount')


def downgrade():
    op.create_table('welcomecount',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('journal', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('submit', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('notify', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('comment', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('note', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='welcomecount_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', name='welcomecount_pkey')
    )
    op.create_index('ind_welcomecount_userid', 'welcomecount', ['userid'], unique=False)

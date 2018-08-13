"""Add permitted senders table

Revision ID: 664a23bbc217
Revises: 36b4c0d45d93
Create Date: 2018-08-06 17:27:11.597444

"""

# revision identifiers, used by Alembic.
revision = '664a23bbc217'
down_revision = '36b4c0d45d93'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('permitted_senders',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('sender', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['sender'], ['login.userid'], name='permitted_senders_sender_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='permitted_senders_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'sender')
    )


def downgrade():
    op.drop_table('permitted_senders')

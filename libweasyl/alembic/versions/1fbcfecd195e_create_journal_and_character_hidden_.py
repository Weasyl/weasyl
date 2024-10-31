"""Create journal and character hidden/friends-only columns

Revision ID: 1fbcfecd195e
Revises: 30ddd5fc6d26
Create Date: 2021-07-26 03:52:04.433272

"""

# revision identifiers, used by Alembic.
revision = '1fbcfecd195e'
down_revision = '30ddd5fc6d26'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('character', sa.Column('friends_only', sa.Boolean(), nullable=True))
    op.add_column('character', sa.Column('hidden', sa.Boolean(), nullable=True))
    op.add_column('journal', sa.Column('friends_only', sa.Boolean(), nullable=True))
    op.add_column('journal', sa.Column('hidden', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('journal', 'hidden')
    op.drop_column('journal', 'friends_only')
    op.drop_column('character', 'hidden')
    op.drop_column('character', 'friends_only')

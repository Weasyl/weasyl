"""Remove forced password resets

Revision ID: 67e810c14252
Revises: 981bd4df447e
Create Date: 2021-03-21 06:53:17.409535

"""

# revision identifiers, used by Alembic.
revision = '67e810c14252'
down_revision = '981bd4df447e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('login', 'force_password_reset')


def downgrade():
    op.add_column('login', sa.Column('force_password_reset', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))

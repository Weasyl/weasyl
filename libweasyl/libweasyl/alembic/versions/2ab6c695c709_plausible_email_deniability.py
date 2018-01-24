"""Add column to support plausible deniability of email addresses.

Revision ID: 2ab6c695c709
Revises: 999833c1fcf9
Create Date: 2017-12-03 00:32:53.266420

"""

# revision identifiers, used by Alembic.
revision = '2ab6c695c709'
down_revision = '999833c1fcf9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('logincreate',
        sa.Column('invalid', sa.Boolean(), nullable=False, server_default='f')
    )


def downgrade():
    op.drop_column('logincreate', 'invalid')

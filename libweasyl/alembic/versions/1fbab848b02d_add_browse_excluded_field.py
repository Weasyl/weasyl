"""Add browse-excluded field
"""

# revision identifiers, used by Alembic.
revision = '1fbab848b02d'
down_revision = 'abac1922735d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('submission', sa.Column('browse_excluded', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('submission', 'browse_excluded')

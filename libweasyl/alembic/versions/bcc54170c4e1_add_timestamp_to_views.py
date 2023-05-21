"""Add timestamp to views

Revision ID: bcc54170c4e1
Revises: ed80016034fd
Create Date: 2021-07-09 02:02:32.644787

"""

# revision identifiers, used by Alembic.
revision = 'bcc54170c4e1'
down_revision = 'ed80016034fd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('views', sa.Column('viewed_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.create_index('ind_views_viewed_at', 'views', ['viewed_at'], unique=False)


def downgrade():
    op.drop_index('ind_views_viewed_at', table_name='views')
    op.drop_column('views', 'viewed_at')

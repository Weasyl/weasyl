"""Add session last_active

Revision ID: 1512aa4220d3
Revises: 571762845c10
Create Date: 2021-08-23 08:01:40.675966

"""

# revision identifiers, used by Alembic.
revision = '1512aa4220d3'
down_revision = '571762845c10'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('sessions', sa.Column('last_active', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.alter_column('sessions', 'last_active', server_default=sa.func.now())
    op.create_index('ind_sessions_last_active', 'sessions', ['last_active'], unique=False)


def downgrade():
    op.drop_index('ind_sessions_last_active', table_name='sessions')
    op.drop_column('sessions', 'last_active')

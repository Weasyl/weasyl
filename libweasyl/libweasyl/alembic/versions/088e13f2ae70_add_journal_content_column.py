"""Add journal content column

Revision ID: 088e13f2ae70
Revises: 7147da2a1adf
Create Date: 2017-08-21 04:34:29.541975

"""

# revision identifiers, used by Alembic.
revision = '088e13f2ae70'
down_revision = '7147da2a1adf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('journal', sa.Column('content', sa.Text(), nullable=True))


def downgrade():
    raise Exception('Reversing this migration could delete new journal content')

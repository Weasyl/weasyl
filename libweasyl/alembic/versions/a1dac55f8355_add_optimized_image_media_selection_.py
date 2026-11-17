"""Add optimized image media selection column

Revision ID: a1dac55f8355
Revises: 7a317ce25845
Create Date: 2020-02-09 02:41:10.113482

"""

# revision identifiers, used by Alembic.
revision = 'a1dac55f8355'
down_revision = '7a317ce25845'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('submission', sa.Column('image_representations', postgresql.BYTEA(), nullable=True))


def downgrade():
    op.drop_column('submission', 'image_representations')

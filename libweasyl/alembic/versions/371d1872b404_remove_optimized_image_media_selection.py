"""Remove optimized image media selection

Revision ID: 371d1872b404
Revises: 30ea79d1586c
Create Date: 2021-03-07 09:41:31.364370

"""

# revision identifiers, used by Alembic.
revision = '371d1872b404'
down_revision = '30ea79d1586c'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_column('submission', 'image_representations')


def downgrade():
    op.add_column('submission', sa.Column('image_representations', postgresql.BYTEA(), autoincrement=False, nullable=True))

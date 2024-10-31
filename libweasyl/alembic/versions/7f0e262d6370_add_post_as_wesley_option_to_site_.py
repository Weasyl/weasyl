"""Add "post as Wesley" option to site updates

Revision ID: 7f0e262d6370
Revises: 8c2635571571
Create Date: 2019-01-09 00:31:23.137018

"""

# revision identifiers, used by Alembic.
revision = '7f0e262d6370'
down_revision = '8c2635571571'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('siteupdate', sa.Column('wesley', sa.Boolean(), server_default='f', nullable=False))


def downgrade():
    op.drop_column('siteupdate', 'wesley')

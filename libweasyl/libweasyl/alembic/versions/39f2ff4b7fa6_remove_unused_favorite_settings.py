"""Remove unused favorite.settings

Revision ID: 39f2ff4b7fa6
Revises: 8e98a1be126e
Create Date: 2019-10-26 20:06:58.166678

"""

# revision identifiers, used by Alembic.
revision = '39f2ff4b7fa6'
down_revision = '8e98a1be126e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('favorite', 'settings')


def downgrade():
    op.add_column('favorite', sa.Column('settings', sa.VARCHAR(length=20), server_default=sa.text(u"''::character varying"), autoincrement=False, nullable=False))

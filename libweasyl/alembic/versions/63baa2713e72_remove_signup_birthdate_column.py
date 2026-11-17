"""Remove signup birthdate column

Revision ID: 63baa2713e72
Revises: 57171ee9e989
Create Date: 2024-08-21 23:50:18.122609

"""

# revision identifiers, used by Alembic.
revision = '63baa2713e72'
down_revision = '57171ee9e989'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('logincreate', 'birthday')


def downgrade():
    op.add_column('logincreate', sa.Column('birthday', sa.INTEGER(), autoincrement=False, nullable=True))

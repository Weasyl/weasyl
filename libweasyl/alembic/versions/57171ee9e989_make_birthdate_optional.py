"""Make birthdate optional

Revision ID: 57171ee9e989
Revises: 9a41d4fa38ba
Create Date: 2023-12-22 00:15:53.754117

"""

# revision identifiers, used by Alembic.
revision = '57171ee9e989'
down_revision = '9a41d4fa38ba'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('logincreate', 'birthday',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.add_column('userinfo', sa.Column('asserted_adult', sa.Boolean(), server_default='f', nullable=False))
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade():
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('userinfo', 'asserted_adult')
    op.alter_column('logincreate', 'birthday',
               existing_type=sa.INTEGER(),
               nullable=False)

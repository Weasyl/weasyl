"""Add login.voucher

Revision ID: 7a317ce25845
Revises: 39f2ff4b7fa6
Create Date: 2020-02-08 02:03:38.777463

"""

# revision identifiers, used by Alembic.
revision = '7a317ce25845'
down_revision = '39f2ff4b7fa6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('login', sa.Column('voucher', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'login', 'login', ['voucher'], ['userid'])
    op.execute('UPDATE login SET voucher = userid')


def downgrade():
    op.drop_constraint(None, 'login', type_='foreignkey')
    op.drop_column('login', 'voucher')

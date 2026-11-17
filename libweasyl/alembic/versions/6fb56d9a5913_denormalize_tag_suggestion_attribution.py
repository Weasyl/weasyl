"""Denormalize tag suggestion attribution

Revision ID: 6fb56d9a5913
Revises: 7a52ff794d57
Create Date: 2023-06-10 08:13:22.369293

"""

# revision identifiers, used by Alembic.
revision = '6fb56d9a5913'
down_revision = '7a52ff794d57'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('searchmapchar', sa.Column('added_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'searchmapchar', 'login', ['added_by'], ['userid'], ondelete='SET NULL')
    op.add_column('searchmapjournal', sa.Column('added_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'searchmapjournal', 'login', ['added_by'], ['userid'], ondelete='SET NULL')
    op.add_column('searchmapsubmit', sa.Column('added_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'searchmapsubmit', 'login', ['added_by'], ['userid'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint(None, 'searchmapsubmit', type_='foreignkey')
    op.drop_column('searchmapsubmit', 'added_by')
    op.drop_constraint(None, 'searchmapjournal', type_='foreignkey')
    op.drop_column('searchmapjournal', 'added_by')
    op.drop_constraint(None, 'searchmapchar', type_='foreignkey')
    op.drop_column('searchmapchar', 'added_by')

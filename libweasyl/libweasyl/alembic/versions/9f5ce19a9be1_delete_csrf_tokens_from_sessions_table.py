"""Delete CSRF tokens from sessions table

Revision ID: 9f5ce19a9be1
Revises: ae725b948f35
Create Date: 2022-07-06 04:28:40.416655

"""

# revision identifiers, used by Alembic.
revision = '9f5ce19a9be1'
down_revision = 'ae725b948f35'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('sessions', 'csrf_token')


def downgrade():
    op.add_column('sessions', sa.Column('csrf_token', sa.VARCHAR(length=64), autoincrement=False, nullable=True))

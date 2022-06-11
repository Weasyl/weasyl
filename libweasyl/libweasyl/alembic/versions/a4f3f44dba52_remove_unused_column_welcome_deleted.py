"""Remove unused column welcome.deleted

Revision ID: a4f3f44dba52
Revises: 5491fc6b3d51
Create Date: 2018-06-17 04:59:21.194645

"""

# revision identifiers, used by Alembic.
revision = 'a4f3f44dba52'
down_revision = '5491fc6b3d51'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_column('welcome', 'deleted')


def downgrade():
    op.add_column('welcome', sa.Column('deleted', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))

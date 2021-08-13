"""Index critique requests

Revision ID: 571762845c10
Revises: e2bedd00b085
Create Date: 2021-08-09 05:05:25.910797

"""

# revision identifiers, used by Alembic.
revision = '571762845c10'
down_revision = 'e2bedd00b085'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ind_submission_submitid_critique', 'submission', ['submitid'], unique=False, postgresql_where=sa.text('critique AND NOT hidden'))


def downgrade():
    op.drop_index('ind_submission_submitid_critique', table_name='submission', postgresql_where=sa.text('critique AND NOT hidden'))

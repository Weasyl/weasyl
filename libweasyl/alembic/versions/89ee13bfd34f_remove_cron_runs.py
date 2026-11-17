"""Remove cron_runs

Revision ID: 89ee13bfd34f
Revises: bcc54170c4e1
Create Date: 2021-07-09 02:08:16.634978

"""

# revision identifiers, used by Alembic.
revision = '89ee13bfd34f'
down_revision = 'bcc54170c4e1'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_table('cron_runs')


def downgrade():
    op.create_table('cron_runs',
    sa.Column('last_run', postgresql.TIMESTAMP(), autoincrement=False, nullable=False)
    )
    op.execute("INSERT INTO cron_runs (last_run) VALUES (TIMESTAMP '2000-01-01 00:00:00')")

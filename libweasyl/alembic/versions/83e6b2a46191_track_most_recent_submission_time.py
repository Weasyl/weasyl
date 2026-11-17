"""Track most recent submission time on profile

Used to prevent scans on submission for determining when
a user most recently posted something, for ordering
marketplace search results

Revision ID: 83e6b2a46191
Revises: a49795aa2584
Create Date: 2017-01-07 03:21:10.114125

"""

# revision identifiers, used by Alembic.
revision = '83e6b2a46191'
down_revision = 'a49795aa2584'

from alembic import op
import sqlalchemy as sa
import libweasyl


def upgrade():
    op.add_column('profile', sa.Column('latest_submission_time', libweasyl.models.helpers.WeasylTimestampColumn(),
                                       nullable=False, server_default='0'))
    op.execute("""
        UPDATE profile p SET latest_submission_time = (
            SELECT COALESCE(MAX(s.unixtime), 0) AS latest FROM submission s WHERE s.userid = p.userid
        )
    """)


def downgrade():
    op.drop_column('profile', 'latest_submission_time')

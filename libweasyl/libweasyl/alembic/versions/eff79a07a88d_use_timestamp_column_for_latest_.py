"""Use TIMESTAMP column for latest submission

Revision ID: eff79a07a88d
Revises: 83e6b2a46191
Create Date: 2017-01-08 22:20:43.814375

"""

# revision identifiers, used by Alembic.
revision = 'eff79a07a88d'
down_revision = '83e6b2a46191'

from alembic import op
import sqlalchemy as sa

import libweasyl
from libweasyl.legacy import UNIXTIME_OFFSET


def upgrade():
    op.alter_column(
        'profile',
        'latest_submission_time',
        new_column_name='latest_submission_time_old',
    )
    op.add_column(
        'profile',
        sa.Column('latest_submission_time', libweasyl.models.helpers.ArrowColumn(), nullable=False, server_default='epoch'),
    )
    op.execute(
        "UPDATE profile SET latest_submission_time = TIMESTAMP WITHOUT TIME ZONE 'epoch' + "
        "(latest_submission_time_old - %d) * INTERVAL '1 second'" % (UNIXTIME_OFFSET,))
    op.drop_column('profile', 'latest_submission_time_old')


def downgrade():
    op.alter_column(
        'profile',
        'latest_submission_time',
        new_column_name='latest_submission_time_new',
    )
    op.add_column(
        'profile',
        sa.Column('latest_submission_time', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False, server_default='0'),
    )
    op.execute(
        "UPDATE profile SET latest_submission_time = extract(epoch from latest_submission_time_new) + %d" % (UNIXTIME_OFFSET,))
    op.drop_column('profile', 'latest_submission_time_new')

"""Delete unused index

Revision ID: dcd68fc5a52e
Revises: 9f5ce19a9be1
Create Date: 2022-07-06 04:30:27.717374

"""

# revision identifiers, used by Alembic.
revision = 'dcd68fc5a52e'
down_revision = '9f5ce19a9be1'

from alembic import op


def upgrade():
    op.drop_index('ind_submission_userid_unixtime', table_name='submission')


def downgrade():
    op.create_index('ind_submission_userid_unixtime', 'submission', ['userid', 'unixtime'], unique=False)

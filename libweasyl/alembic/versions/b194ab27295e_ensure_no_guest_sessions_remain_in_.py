"""Ensure no guest sessions remain in database

Revision ID: b194ab27295e
Revises: 5491fc6b3d51
Create Date: 2018-06-19 23:06:42.395887

"""

# revision identifiers, used by Alembic.
revision = 'b194ab27295e'
down_revision = '5491fc6b3d51'

from alembic import op


def upgrade():
    op.create_check_constraint(
        'sessions_no_guest_check',
        'sessions',
        "userid IS NOT NULL OR additional_data != ''",
    )


def downgrade():
    op.drop_constraint('sessions_no_guest_check', 'sessions')

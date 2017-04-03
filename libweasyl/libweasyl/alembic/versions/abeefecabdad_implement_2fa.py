"""
Implements two-factor authentication.

Revision ID: abeefecabdad
Revises: 40c00abab5f9
Create Date: 2017-01-19 01:56:20.093477

"""

# revision identifiers, used by Alembic.
revision = 'abeefecabdad'
down_revision = '40c00abab5f9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create a table to store 2FA backup codes for use when the authenticator is unavailable.
    op.create_table('twofa_recovery_codes',
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.Column('recovery_code', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('userid', 'recovery_code'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='twofa_recovery_codes_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    )
    op.create_index('ind_twofa_recovery_codes_userid', 'twofa_recovery_codes', ['userid'])

    # Modify `login` to hold the 2FA code (if set) for a user account
    op.add_column(
        'login',
        sa.Column('twofa_secret', sa.String(length=420), nullable=True, server_default=None),
    )


def downgrade():
    # Remove 2FA logic of recovery codes and secret
    op.drop_index('ind_twofa_recovery_codes_userid', 'twofa_recovery_codes')
    op.drop_table('twofa_recovery_codes')
    op.drop_column('login', 'twofa_secret')

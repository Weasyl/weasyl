"""Verify email addresses before changing.

Leverage the existing `emailverify` table (which was unused) to store an email prior to changing
the email on an account, requiring the user to provide a token to confirm ownership of the email
before changing the email on the user's account.

Revision ID: b2df373af9f7
Revises: 3f18ecfaf637
Create Date: 2017-03-15 01:09:34.651344
"""

# revision identifiers, used by Alembic.
revision = 'b2df373af9f7'
down_revision = '3f18ecfaf637'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Alter the ``emailverify`` table to hold a timestamp and token, and add an
    index for fast searches for the token.
    """
    op.add_column('emailverify',
        sa.Column('createtimestamp', sa.DateTime(timezone=True), server_default=sa.text(u'now()'), nullable=False)
    )
    op.add_column('emailverify',
        sa.Column('token', sa.String(length=100), nullable=False)
    )
    op.create_index('ind_emailverify_token', 'emailverify', ['token'], unique=False)


def downgrade():
    """
    On downgrade, drop the created index, ``token`` and ``createtimestamp`` columns that we added during ``upgrade()``
    """
    op.drop_index('ind_emailverify_token', table_name='emailverify')
    op.drop_column('emailverify', 'token')
    op.drop_column('emailverify', 'createtimestamp')

"""Store invalid email in logincreate records to permit viewing pending records.

Revision ID: 8cde5e07b63f
Revises: 2ab6c695c709
Create Date: 2018-01-16 00:36:43.973449

"""

# revision identifiers, used by Alembic.
revision = '8cde5e07b63f'
down_revision = '2ab6c695c709'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Provide a column to store the original email address so admins can view pending accounts, and know if an email
    # collided with one that is in use (logincreate.email is a unique field, so we can't use that to store the email).
    op.add_column('logincreate', sa.Column('invalid_email_addr', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('logincreate', 'invalid_email_addr')

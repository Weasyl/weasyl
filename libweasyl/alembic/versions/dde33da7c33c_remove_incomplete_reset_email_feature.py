"""Remove incomplete reset-email feature

Revision ID: dde33da7c33c
Revises: 0dd45a91821c
Create Date: 2019-10-13 14:35:35.522626

"""

# revision identifiers, used by Alembic.
revision = 'dde33da7c33c'
down_revision = '0dd45a91821c'

from alembic import op


def upgrade():
    op.execute("UPDATE login SET settings = replace(settings, 'e', '') WHERE settings ~ 'e'")


def downgrade():
    pass

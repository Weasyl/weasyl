"""Add submission tag history index

Revision ID: af3b8d60b7ba
Revises: bcb0d75b6f8b
Create Date: 2021-07-23 02:04:11.970503

"""

# revision identifiers, used by Alembic.
revision = 'af3b8d60b7ba'
down_revision = 'bcb0d75b6f8b'

from alembic import op


def upgrade():
    op.create_index('ind_tag_updates_submitid', 'tag_updates', ['submitid'], unique=False)


def downgrade():
    op.drop_index('ind_tag_updates_submitid', table_name='tag_updates')

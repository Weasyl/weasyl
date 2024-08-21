"""Index media by sha256

Revision ID: c8c088918278
Revises: 48ab4dc5599f
Create Date: 2016-07-06 11:47:57.436197

"""

# revision identifiers, used by Alembic.
revision = 'c8c088918278'
down_revision = '48ab4dc5599f'

from alembic import op


def upgrade():
    op.create_index('ind_media_sha256', 'media', ['sha256'], unique=False)


def downgrade():
    op.drop_index('ind_media_sha256', table_name='media')

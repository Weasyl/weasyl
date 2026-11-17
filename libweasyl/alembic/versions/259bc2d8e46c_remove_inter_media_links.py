"""Remove inter-media links

Revision ID: 259bc2d8e46c
Revises: 67e810c14252
Create Date: 2021-06-26 18:09:59.780429

"""

# revision identifiers, used by Alembic.
revision = '259bc2d8e46c'
down_revision = '67e810c14252'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index('ind_media_media_links_described_with_id', table_name='media_media_links')
    op.drop_index('ind_media_media_links_describee_id', table_name='media_media_links')
    op.drop_index('ind_media_media_links_submitid', table_name='media_media_links')
    op.drop_table('media_media_links')


def downgrade():
    op.create_table('media_media_links',
    sa.Column('linkid', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('described_with_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('describee_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('link_type', sa.VARCHAR(length=32), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['described_with_id'], ['media.mediaid'], name='media_media_links_described_with_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['describee_id'], ['media.mediaid'], name='media_media_links_describee_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('linkid', name='media_media_links_pkey')
    )
    op.create_index('ind_media_media_links_submitid', 'media_media_links', ['describee_id'], unique=False)
    op.create_index('ind_media_media_links_describee_id', 'media_media_links', ['describee_id'], unique=False)
    op.create_index('ind_media_media_links_described_with_id', 'media_media_links', ['described_with_id'], unique=False)

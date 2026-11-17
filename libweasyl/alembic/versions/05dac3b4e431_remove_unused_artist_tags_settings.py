"""Remove unused artist tags settings"""

revision = '05dac3b4e431'
down_revision = '40c00abab5f9'

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.drop_index(op.f('ind_artist_optout_tags_tagid'), table_name='artist_optout_tags')
    op.drop_column('artist_optout_tags', 'settings')
    op.drop_index(op.f('ind_artist_preferred_tags_tagid'), table_name='artist_preferred_tags')
    op.drop_column('artist_preferred_tags', 'settings')


def downgrade() -> None:
    op.add_column('artist_preferred_tags', sa.Column('settings', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.create_index(op.f('ind_artist_preferred_tags_tagid'), 'artist_preferred_tags', ['tagid'], unique=False)
    op.add_column('artist_optout_tags', sa.Column('settings', sa.VARCHAR(), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.create_index(op.f('ind_artist_optout_tags_tagid'), 'artist_optout_tags', ['tagid'], unique=False)

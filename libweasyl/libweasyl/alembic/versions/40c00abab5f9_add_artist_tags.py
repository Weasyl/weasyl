"""Add artist tags

This relation links tags to an artist, allowing them to tag
themselves with types of content that they prefer to create
or will not create. This is done in the interest of providing
a more meaningful commission search by increasing the search
rank when an artist's strengths match the content requested.

Revision ID: 40c00abab5f9
Revises: 83e6b2a46191
Create Date: 2016-09-23 01:56:20.093477

"""

# revision identifiers, used by Alembic.
revision = '40c00abab5f9'
down_revision = '83e6b2a46191'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('artist_preferred_tags',
                    sa.Column('tagid', sa.Integer(), nullable=False),
                    sa.Column('targetid', sa.Integer(), nullable=False),
                    sa.Column('settings', sa.String(), server_default='', nullable=False),
                    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['targetid'], ['login.userid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('tagid', 'targetid')
                    )
    op.create_index('ind_artist_preferred_tags_tagid', 'artist_preferred_tags', ['tagid'])
    op.create_index('ind_artist_preferred_tags_targetid', 'artist_preferred_tags', ['targetid'])

    op.create_table('artist_optout_tags',
                    sa.Column('tagid', sa.Integer(), nullable=False),
                    sa.Column('targetid', sa.Integer(), nullable=False),
                    sa.Column('settings', sa.String(), server_default='', nullable=False),
                    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['targetid'], ['login.userid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('tagid', 'targetid')
                    )
    op.create_index('ind_artist_optout_tags_tagid', 'artist_optout_tags', ['tagid'])
    op.create_index('ind_artist_optout_tags_targetid', 'artist_optout_tags', ['targetid'])
    op.execute('CREATE EXTENSION IF NOT EXISTS FUZZYSTRMATCH')


def downgrade():
    op.drop_index('ind_artist_preferred_tags_tagid', 'artist_preferred_tags')
    op.drop_index('ind_artist_preferred_tags_targetid', 'artist_preferred_tags')
    op.drop_table('artist_preferred_tags')
    op.drop_index('ind_artist_optout_tags_tagid', 'artist_optout_tags')
    op.drop_index('ind_artist_optout_tags_targetid', 'artist_optout_tags')
    op.drop_table('artist_optout_tags')
    op.execute('DROP EXTENSION IF EXISTS FUZZYSTRMATCH')

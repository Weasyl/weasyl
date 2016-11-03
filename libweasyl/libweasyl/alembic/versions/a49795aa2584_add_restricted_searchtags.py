"""
Add tables to support user and globally restricted searchtags, which prevent tags from
being added to content items.

Revision ID: a49795aa2584
Revises: 882fe6ace5c7
Create Date: 2016-10-01 03:00:22.859648

"""

# revision identifiers, used by Alembic.
revision = 'a49795aa2584'
down_revision = '882fe6ace5c7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create the table/index for user blacklist of searchtags
    op.create_table('searchmapuserrestrictedtags',
        sa.Column('tagid', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapuserrestrictedtags_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='searchmapuserrestrictedtags_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_searchmapuserrestrictedtags_tagid', 'searchmapuserrestrictedtags', ['tagid'], unique=False)
    op.create_index('ind_searchmapuserrestrictedtags_userid', 'searchmapuserrestrictedtags', ['userid'], unique=False)

    # Create the table/index for global blacklist of searchtags
    op.create_table('searchmapglobalrestrictedtags',
        sa.Column('tagid', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapglobalrestrictedtags_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='searchmapglobalrestrictedtags_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_searchmapglobalrestrictedtags_tagid', 'searchmapglobalrestrictedtags', ['tagid'], unique=False)
    op.create_index('ind_searchmapglobalrestrictedtags_userid', 'searchmapglobalrestrictedtags', ['userid'], unique=False)


def downgrade():
    # Drop the table/index for user blacklist of searchtags
    op.drop_index('ind_searchmapuserrestrictedtags_tagid', table_name='searchmapuserrestrictedtags')
    op.drop_index('ind_searchmapuserrestrictedtags_userid', table_name='searchmapuserrestrictedtags')
    op.drop_table('searchmapuserrestrictedtags')

    # Drop the table/index for global blacklist of searchtags
    op.drop_index('ind_searchmapglobalrestrictedtags_tagid', table_name='searchmapglobalrestrictedtags')
    op.drop_index('ind_searchmapglobalrestrictedtags_userid', table_name='searchmapglobalrestrictedtags')
    op.drop_table('searchmapglobalrestrictedtags')

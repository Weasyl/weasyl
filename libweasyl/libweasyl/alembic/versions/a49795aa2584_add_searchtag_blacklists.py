"""Add searchtag blacklists

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
    op.create_table('searchmapuserblacklist',
        sa.Column('tagid', sa.Integer(), nullable=False),     # noqa: E128
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapuserblacklist_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='searchmapuserblacklist_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_searchmapuserblacklist_tagid', 'searchmapuserblacklist', ['tagid'], unique=False)
    op.create_index('ind_searchmapuserblacklist_userid', 'searchmapuserblacklist', ['userid'], unique=False)

    # Create the table/index for global blacklist of searchtags
    op.create_table('searchmapglobalblacklist',
        sa.Column('tagid', sa.Integer(), nullable=False),     # noqa: E128
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapglobalblacklist_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='searchmapglobalblacklist_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_searchmapglobalblacklist_tagid', 'searchmapglobalblacklist', ['tagid'], unique=False)
    op.create_index('ind_searchmapglobalblacklist_userid', 'searchmapglobalblacklist', ['userid'], unique=False)     


def downgrade():
    # Drop the table/index for user blacklist of searchtags
    op.drop_index('ind_searchmapuserblacklist_tagid', table_name='searchmapuserblacklist')
    op.drop_index('ind_searchmapuserblacklist_userid', table_name='searchmapuserblacklist')
    op.drop_table('searchmapuserblacklist')

    # Drop the table/index for global blacklist of searchtags
    op.drop_index('ind_searchmapglobalblacklist_tagid', table_name='searchmapglobalblacklist')
    op.drop_index('ind_searchmapglobalblacklist_userid', table_name='searchmapglobalblacklist')
    op.drop_table('searchmapglobalblacklist')    

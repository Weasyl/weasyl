"""Add artist tags

This relation links tags to an artist, allowing them to tag
themselves with types of content that they prefer to create
or will not create. This is done in the interest of providing
a more meaningful commission search by increasing the search
rank when an artist's strengths match the content requested.

Revision ID: 40c00abab5f9
Revises: c8c088918278
Create Date: 2016-09-23 01:56:20.093477

"""

# revision identifiers, used by Alembic.
revision = '40c00abab5f9'
down_revision = 'c8c088918278'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('searchmapartist',
                    sa.Column('tagid', sa.Integer(), nullable=False),
                    sa.Column('targetid', sa.Integer(), nullable=False),
                    sa.Column('settings', sa.String(), server_default='', nullable=False),
                    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['targetid'], ['login.userid'], onupdate='CASCADE', ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('tagid', 'targetid')
                    )
    op.create_index('ind_searchmapartist_tagid', 'searchmapartist', ['tagid'])
    op.create_index('ind_searchmapartist_targetid', 'searchmapartist', ['targetid'])


def downgrade():
    op.drop_table('searchmapartist')
    op.drop_index('ind_searchmapartist_tagid', 'searchmapartist')
    op.drop_index('ind_searchmapartist_targetid', 'searchmapartist')

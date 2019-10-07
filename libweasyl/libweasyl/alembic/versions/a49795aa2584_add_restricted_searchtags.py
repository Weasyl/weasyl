"""
Add tables to support user and globally restricted searchtags.

Revision ID: a49795aa2584
Revises: 882fe6ace5c7
Create Date: 2016-10-01 03:00:22.859648

"""

# revision identifiers, used by Alembic.
revision = 'a49795aa2584'
down_revision = '882fe6ace5c7'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    # Create the table/index for user restricted tags
    op.create_table('user_restricted_tags',
        sa.Column('tagid', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='user_restricted_tags_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_restricted_tags_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_user_restricted_tags_tagid', 'user_restricted_tags', ['tagid'], unique=False)
    op.create_index('ind_user_restricted_tags_userid', 'user_restricted_tags', ['userid'], unique=False)

    # Create the table/index for globally restricted tags
    op.create_table('globally_restricted_tags',
        sa.Column('tagid', sa.Integer(), nullable=False),
        sa.Column('userid', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='globally_restricted_tags_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='globally_restricted_tags_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tagid', 'userid')
    )
    op.create_index('ind_globally_restricted_tags_tagid', 'globally_restricted_tags', ['tagid'], unique=False)
    op.create_index('ind_globally_restricted_tags_userid', 'globally_restricted_tags', ['userid'], unique=False)


def downgrade():
    # Drop the table/index for user restricted tags
    op.drop_index('ind_user_restricted_tags_tagid', table_name='user_restricted_tags')
    op.drop_index('ind_user_restricted_tags_userid', table_name='user_restricted_tags')
    op.drop_table('user_restricted_tags')

    # Drop the table/index for globally restricted tags
    op.drop_index('ind_globally_restricted_tags_tagid', table_name='globally_restricted_tags')
    op.drop_index('ind_globally_restricted_tags_userid', table_name='globally_restricted_tags')
    op.drop_table('globally_restricted_tags')

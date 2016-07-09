"""Add submission_tags for fast searching

Revision ID: 9afc9a45510c
Revises: abac1922735d
Create Date: 2016-06-13 14:40:01.782784

"""

# revision identifiers, used by Alembic.
revision = '9afc9a45510c'
down_revision = 'abac1922735d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('submission_tags',
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('tags', postgresql.ARRAY(sa.Integer()), nullable=False),
    sa.ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='submission_tags_submitid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('submitid')
    )
    op.execute(
        'INSERT INTO submission_tags (submitid, tags) '
        'SELECT targetid, array_agg(tagid) FROM searchmapsubmit GROUP BY targetid')
    op.create_index('ind_submission_tags_tags', 'submission_tags', ['tags'], unique=False, postgresql_using='gin')


def downgrade():
    op.drop_index('ind_submission_tags_tags', table_name='submission_tags')
    op.drop_table('submission_tags')

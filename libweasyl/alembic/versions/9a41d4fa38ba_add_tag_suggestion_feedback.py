"""Add tag suggestion feedback

Revision ID: 9a41d4fa38ba
Revises: 6fb56d9a5913
Create Date: 2023-06-25 23:20:10.816058

"""

# revision identifiers, used by Alembic.
revision = '9a41d4fa38ba'
down_revision = '6fb56d9a5913'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('tag_suggestion_feedback_character',
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('last_modified', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('incorrect', sa.Boolean(), nullable=False),
    sa.Column('unwanted', sa.Boolean(), nullable=False),
    sa.Column('abusive', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], ),
    sa.ForeignKeyConstraint(['targetid'], ['character.charid'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('targetid', 'tagid', 'userid')
    )
    op.create_table('tag_suggestion_feedback_journal',
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('last_modified', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('incorrect', sa.Boolean(), nullable=False),
    sa.Column('unwanted', sa.Boolean(), nullable=False),
    sa.Column('abusive', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], ),
    sa.ForeignKeyConstraint(['targetid'], ['journal.journalid'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('targetid', 'tagid', 'userid')
    )
    op.create_table('tag_suggestion_feedback_submission',
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('last_modified', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('incorrect', sa.Boolean(), nullable=False),
    sa.Column('unwanted', sa.Boolean(), nullable=False),
    sa.Column('abusive', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], ),
    sa.ForeignKeyConstraint(['targetid'], ['submission.submitid'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('targetid', 'tagid', 'userid')
    )


def downgrade():
    op.drop_table('tag_suggestion_feedback_submission')
    op.drop_table('tag_suggestion_feedback_journal')
    op.drop_table('tag_suggestion_feedback_character')

"""Remove Akismet spam queue is_spam columns

Revision ID: 30ea79d1586c
Revises: 77c5bbd1fa3d
Create Date: 2020-04-04 02:09:15.162190

"""

# revision identifiers, used by Alembic.
revision = '30ea79d1586c'
down_revision = '77c5bbd1fa3d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index('ind_journal_is_spam', table_name='journal')
    op.drop_column('journal', 'is_spam')
    op.drop_index('ind_submission_is_spam', table_name='submission')
    op.drop_column('submission', 'is_spam')


def downgrade():
    op.add_column('submission', sa.Column('is_spam', sa.BOOLEAN(), server_default=sa.text(u'false'), autoincrement=False, nullable=False))
    op.create_index('ind_submission_is_spam', 'submission', ['is_spam'], unique=False)
    op.add_column('journal', sa.Column('is_spam', sa.BOOLEAN(), server_default=sa.text(u'false'), autoincrement=False, nullable=False))
    op.create_index('ind_journal_is_spam', 'journal', ['is_spam'], unique=False)

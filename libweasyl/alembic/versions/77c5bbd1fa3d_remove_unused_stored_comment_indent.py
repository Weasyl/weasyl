"""Remove unused stored comment indent

Revision ID: 77c5bbd1fa3d
Revises: c5074772185a
Create Date: 2020-04-03 06:12:36.855188

"""

# revision identifiers, used by Alembic.
revision = '77c5bbd1fa3d'
down_revision = 'c5074772185a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('charcomment', 'indent')
    op.drop_column('comments', 'indent')
    op.drop_column('journalcomment', 'indent')


def downgrade():
    op.add_column('journalcomment', sa.Column('indent', sa.INTEGER(), server_default=sa.text(u'0'), autoincrement=False, nullable=False))
    op.add_column('comments', sa.Column('indent', sa.INTEGER(), server_default=sa.text(u'0'), autoincrement=False, nullable=False))
    op.add_column('charcomment', sa.Column('indent', sa.INTEGER(), server_default=sa.text(u'0'), autoincrement=False, nullable=False))

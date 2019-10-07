"""Create table to block specified email providers during signup

Revision ID: 882fe6ace5c7
Revises: cbe0ea91af79
Create Date: 2016-07-17 23:02:31.217495

"""

# revision identifiers, used by Alembic.
revision = '882fe6ace5c7'
down_revision = 'cbe0ea91af79'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.create_table('emailblacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_name', sa.String(length=252), nullable=False),
        sa.Column('added_by', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['added_by'], ['login.userid'], name='emailblacklist_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain_name')
    )
    op.create_index('ind_emailblacklist_domain_name', 'emailblacklist', ['domain_name'], unique=False)


def downgrade():
    op.drop_index('ind_emailblacklist_domain_name', table_name='emailblacklist')
    op.drop_table('emailblacklist')

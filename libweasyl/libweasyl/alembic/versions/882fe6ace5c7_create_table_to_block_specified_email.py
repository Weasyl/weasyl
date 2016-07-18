"""Create table to block specified email providers during signup

Revision ID: 882fe6ace5c7
Revises: c8c088918278
Create Date: 2016-07-17 23:02:31.217495

"""

# revision identifiers, used by Alembic.
revision = '882fe6ace5c7'
down_revision = 'c8c088918278'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('emailblacklist',
        sa.Column('domain_name_id', sa.Integer(), nullable=False),
        sa.Column('domain_name', sa.String(length=256), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('domain_name_id'),
        sa.UniqueConstraint('domain_name')
    )
    op.create_index('ind_emailblacklist_domain_name', 'emailblacklist', ['domain_name'], unique=False)


def downgrade():
    op.drop_index('ind_emailblacklist_domain_name', table_name='emailblacklist')
    op.drop_table('emailblacklist')

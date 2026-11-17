"""Remove emailblacklist"""

revision = '153c4e330657'
down_revision = '5a073c92aab9'

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.drop_table('emailblacklist')


def downgrade() -> None:
    op.create_table('emailblacklist',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('domain_name', sa.VARCHAR(length=252), autoincrement=False, nullable=False),
    sa.Column('added_by', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('reason', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['added_by'], ['login.userid'], name=op.f('emailblacklist_userid_fkey'), deferrable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('emailblacklist_pkey')),
    sa.UniqueConstraint('domain_name', name=op.f('emailblacklist_domain_name_key'))
    )

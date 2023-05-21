"""Remove time zone preferences

Revision ID: ae725b948f35
Revises: 1512aa4220d3
Create Date: 2022-07-06 04:22:25.316880

"""

# revision identifiers, used by Alembic.
revision = 'ae725b948f35'
down_revision = '1512aa4220d3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('user_timezones')


def downgrade():
    op.create_table('user_timezones',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('timezone', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_timezones_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', name='user_timezones_pkey')
    )

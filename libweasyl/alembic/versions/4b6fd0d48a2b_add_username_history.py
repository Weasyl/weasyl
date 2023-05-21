"""Add username history

Revision ID: 4b6fd0d48a2b
Revises: c1f8375b5805
Create Date: 2020-02-19 18:51:51.714126

"""

# revision identifiers, used by Alembic.
revision = '4b6fd0d48a2b'
down_revision = 'c1f8375b5805'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('username_history',
    sa.Column('historyid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=25), nullable=False),
    sa.Column('login_name', sa.String(length=25), nullable=False),
    sa.Column('replaced_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('replaced_by', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('deactivated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('deactivated_by', sa.Integer(), nullable=True),
    sa.Column('cosmetic', sa.Boolean(), nullable=False),
    sa.CheckConstraint(u"login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g'))", name='username_history_login_name_check'),
    sa.CheckConstraint(u"username !~ '[^ -~]' AND username !~ ';'", name='username_history_username_check'),
    sa.CheckConstraint(u'NOT (cosmetic AND active)', name='username_history_cosmetic_inactive_check'),
    sa.CheckConstraint(u'(active OR cosmetic) = (deactivated_at IS NULL) AND (active OR cosmetic) = (deactivated_by IS NULL)', name='username_history_active_check'),
    sa.ForeignKeyConstraint(['deactivated_by'], ['login.userid'], ),
    sa.ForeignKeyConstraint(['replaced_by'], ['login.userid'], ),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], ),
    sa.PrimaryKeyConstraint('historyid')
    )
    op.create_index('ind_username_history_login_name', 'username_history', ['login_name'], unique=True, postgresql_where=sa.text('active'))
    op.create_index('ind_username_history_userid', 'username_history', ['userid'], unique=True, postgresql_where=sa.text('active'))
    op.create_index('ind_username_history_userid_historyid', 'username_history', ['userid', 'historyid'], unique=True, postgresql_where=sa.text(u'NOT cosmetic'))


def downgrade():
    op.drop_index('ind_username_history_userid_historyid', table_name='username_history')
    op.drop_index('ind_username_history_userid', table_name='username_history')
    op.drop_index('ind_username_history_login_name', table_name='username_history')
    op.drop_table('username_history')

"""Improve password reset

Revision ID: c5074772185a
Revises: 3accc3d526ba
Create Date: 2020-03-28 03:11:19.300735

"""

# revision identifiers, used by Alembic.
revision = 'c5074772185a'
down_revision = '3accc3d526ba'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_index(
        'ind_login_lower_email',
        'login',
        [
            sa.text('(lower(email COLLATE "C"))'),
        ],
        unique=False,
    )
    op.drop_table('forgotpassword')
    op.create_table('forgotpassword',
    sa.Column('token_sha256', postgresql.BYTEA(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.PrimaryKeyConstraint('token_sha256')
    )
    op.create_index('ind_forgotpassword_created_at', 'forgotpassword', ['created_at'], unique=False)
    op.create_table('user_events',
    sa.Column('eventid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('event', sa.String(length=100), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('occurred', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], ),
    sa.PrimaryKeyConstraint('eventid')
    )
    op.create_index('ind_user_events_userid_eventid', 'user_events', ['userid', 'eventid'], unique=False)


def downgrade():
    op.drop_index('ind_login_lower_email', table_name='login')

    op.drop_table('forgotpassword')
    op.create_table('forgotpassword',
    sa.Column('set_time', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('address', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('link_time', sa.INTEGER(), server_default=sa.text(u'0'), autoincrement=False, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('token', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], [u'login.userid'], name=u'forgotpassword_userid_fkey', onupdate=u'CASCADE', ondelete=u'CASCADE'),
    sa.UniqueConstraint('userid', name=u'forgotpassword_userid_key')
    )
    op.drop_index('ind_user_events_userid_eventid', table_name='user_events')
    op.drop_table('user_events')
    op.drop_index('ind_forgotpassword_created_at', table_name='forgotpassword')

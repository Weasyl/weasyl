"""Split login charsettings to columns, removing birthday reset

Revision ID: c1f8375b5805
Revises: 54229aa716bc
Create Date: 2020-02-14 02:29:53.525649

"""

# revision identifiers, used by Alembic.
revision = 'c1f8375b5805'
down_revision = '54229aa716bc'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.add_column('login', sa.Column('force_password_reset', sa.Boolean(), server_default='f', nullable=False))
    op.execute("UPDATE login SET force_password_reset = TRUE WHERE settings ~ 'p'")

    op.add_column('login', sa.Column('is_banned', sa.Boolean(), server_default='f', nullable=False))
    op.execute("UPDATE login SET is_banned = TRUE WHERE settings ~ 'b'")

    op.add_column('login', sa.Column('is_suspended', sa.Boolean(), server_default='f', nullable=False))
    op.execute("UPDATE login SET is_suspended = TRUE WHERE settings ~ 's'")

    op.drop_column('login', 'settings')


def downgrade():
    op.add_column('login', sa.Column('settings', sa.VARCHAR(length=20), server_default=sa.text(u"''::character varying"), autoincrement=False, nullable=False))
    op.execute("UPDATE login SET settings = settings || 'p' WHERE force_password_reset")
    op.execute("UPDATE login SET settings = settings || 'b' WHERE is_banned")
    op.execute("UPDATE login SET settings = settings || 's' WHERE is_suspended")

    op.drop_column('login', 'is_suspended')
    op.drop_column('login', 'is_banned')
    op.drop_column('login', 'force_password_reset')

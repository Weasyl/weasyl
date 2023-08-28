"""Split login charsettings to columns, removing birthday reset

Removes login.settings, replacing with a distinct column (login.force_password_reset) for forced password resets.
Drops forced resets of birthdays entirely, and opts to leverage existing permaban/suspension tables for determining
if a user is banned or suspended.

Revision ID: c1f8375b5805
Revises: 54229aa716bc
Create Date: 2020-02-14 02:29:53.525649

"""

# revision identifiers, used by Alembic.
revision = 'c1f8375b5805'
down_revision = '54229aa716bc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('login', sa.Column('force_password_reset', sa.Boolean(), server_default='f', nullable=False))
    op.execute("UPDATE login SET force_password_reset = TRUE WHERE settings ~ 'p'")

    # NB: Bans/suspensions based on the contents of the permaban/suspension tables, so no replacement column needed
    # during upgrade()

    op.drop_column('login', 'settings')


def downgrade():
    op.add_column('login', sa.Column('settings', sa.VARCHAR(length=20), server_default=sa.text(u"''::character varying"), autoincrement=False, nullable=False))
    op.execute("UPDATE login SET settings = settings || 'p' WHERE force_password_reset")

    # Restore the ban flag ('b')
    op.execute("""
        UPDATE login
        SET settings = settings || 'b'
        FROM permaban
        WHERE login.userid = permaban.userid
    """)

    # Restore the suspended flag ('s')
    op.execute("""
        UPDATE login
        SET settings = login.settings || 's'
        FROM suspension
        WHERE login.userid = suspension.userid
    """)

    op.drop_column('login', 'force_password_reset')

"""Remove boolean settings that have their own columns

Revision ID: eea0490be1f8
Revises: dcd68fc5a52e
Create Date: 2022-07-06 04:37:00.864230

"""

# revision identifiers, used by Alembic.
revision = 'eea0490be1f8'
down_revision = 'dcd68fc5a52e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('journal', 'settings')
    op.execute("UPDATE character SET settings = regexp_replace(settings, '[fh]', '', 'g') WHERE settings ~ '[fh]'")


def downgrade():
    op.add_column('journal', sa.Column('settings', sa.VARCHAR(length=20), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.execute("UPDATE journal SET settings = settings || 'h' WHERE hidden")
    op.execute("UPDATE journal SET settings = settings || 'f' WHERE friends_only")
    op.execute("UPDATE character SET settings = settings || 'h' WHERE hidden")
    op.execute("UPDATE character SET settings = settings || 'f' WHERE friends_only")

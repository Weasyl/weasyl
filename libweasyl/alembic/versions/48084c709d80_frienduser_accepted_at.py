"""frienduser.accepted_at

Revision ID: 48084c709d80
Revises: 6421032c567d
Create Date: 2026-01-15 08:29:37.656586

"""

# revision identifiers, used by Alembic.
revision = '48084c709d80'
down_revision = '6421032c567d'

from alembic import op
import sqlalchemy as sa
from psycopg2.errors import DuplicateObject
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.add_column('frienduser', sa.Column('accepted_at', postgresql.TIMESTAMP(timezone=True), nullable=True), if_not_exists=True)

        try:
            op.execute("ALTER TABLE frienduser ADD CONSTRAINT frienduser_accepted_at_check CHECK (accepted_at IS NULL OR settings = '') NOT VALID")
        except sa.exc.ProgrammingError as e:
            if not isinstance(e.orig, DuplicateObject):
                raise

        op.execute("ALTER TABLE frienduser VALIDATE CONSTRAINT frienduser_accepted_at_check")


def downgrade() -> None:
    op.drop_constraint('frienduser_accepted_at_check', 'frienduser')
    op.drop_column('frienduser', 'accepted_at')

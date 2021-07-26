"""Fill journal and character hidden/friends-only columns

Revision ID: e2bedd00b085
Revises: 1fbcfecd195e
Create Date: 2021-07-26 05:43:43.742595

"""

# revision identifiers, used by Alembic.
revision = 'e2bedd00b085'
down_revision = '1fbcfecd195e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


BATCH_SIZE = 10_000


def upgrade():
    context = op.get_context()

    with context.autocommit_block():
        max_charid = context.bind.scalar(text("SELECT max(charid) FROM character"))

        for i in range(1, max_charid + 1, BATCH_SIZE):
            context.bind.execute(
                text("UPDATE character SET hidden = settings ~ 'h', friends_only = settings ~ 'f' WHERE (charid BETWEEN :start AND :end) AND (hidden IS NULL OR friends_only IS NULL)"),
                {"start": i, "end": i + BATCH_SIZE - 1},
            )

        context.bind.execute(
            text("UPDATE character SET hidden = settings ~ 'h', friends_only = settings ~ 'f' WHERE (hidden IS NULL OR friends_only IS NULL)"),
        )

        max_journalid = context.bind.scalar(text("SELECT max(journalid) FROM journal"))

        for i in range(1, max_journalid + 1, BATCH_SIZE):
            context.bind.execute(
                text("UPDATE journal SET hidden = settings ~ 'h', friends_only = settings ~ 'f' WHERE (journalid BETWEEN :start AND :end) AND (hidden IS NULL OR friends_only IS NULL)"),
                {"start": i, "end": i + BATCH_SIZE - 1},
            )

        context.bind.execute(
            text("UPDATE journal SET hidden = settings ~ 'h', friends_only = settings ~ 'f' WHERE (hidden IS NULL OR friends_only IS NULL)"),
        )

    op.alter_column('character', 'hidden',
               existing_type=sa.BOOLEAN(),
               server_default='f',
               nullable=False)
    op.alter_column('character', 'friends_only',
               existing_type=sa.BOOLEAN(),
               server_default='f',
               nullable=False)
    op.alter_column('journal', 'hidden',
               existing_type=sa.BOOLEAN(),
               server_default='f',
               nullable=False)
    op.alter_column('journal', 'friends_only',
               existing_type=sa.BOOLEAN(),
               server_default='f',
               nullable=False)


def downgrade():
    op.alter_column('character', 'hidden',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               nullable=True)
    op.alter_column('character', 'friends_only',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               nullable=True)
    op.alter_column('journal', 'hidden',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               nullable=True)
    op.alter_column('journal', 'friends_only',
               existing_type=sa.BOOLEAN(),
               server_default=None,
               nullable=True)

"""mail-out rate limit

Revision ID: aad971c115bf
Revises: None
Create Date: 2025-12-29 08:19:04.468181

"""

# revision identifiers, used by Alembic.
revision = 'aad971c115bf'
down_revision = None

from alembic import op
import sqlalchemy as sa

from weasyl.rate_limits import RateLimitId


def upgrade():
    op.create_table('global_rate_limits',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('available', sa.Integer(), server_default='0', nullable=False),
    sa.Column('last_update', sa.BigInteger(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.bulk_insert(
        sa.table('global_rate_limits', sa.column('id')),
        [
            {'id': op.inline_literal(RateLimitId.MAIL_OUT.value)},
        ],
        multiinsert=False,
    )


def downgrade():
    op.drop_table('global_rate_limits')

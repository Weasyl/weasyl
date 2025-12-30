"""Birthday from WeasylTimestampColumn to date

Revision ID: e8baabdecd2f
Revises: 63baa2713e72
Create Date: 2020-03-14 13:18:55.552000

"""

# revision identifiers, used by Alembic.
revision = 'e8baabdecd2f'
down_revision = '63baa2713e72'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.INTEGER(),
               type_=sa.Date(),
               existing_nullable=True,
               postgresql_using="(to_timestamp(birthday + 18000) AT TIME ZONE 'UTC')::date")


def downgrade():
    op.alter_column('userinfo', 'birthday',
               existing_type=sa.Date(),
               type_=sa.INTEGER(),
               existing_nullable=True,
               postgresql_using="extract(epoch from birthday) - 18000")

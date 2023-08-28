"""Remove moderate rating from SFW settings

Revision ID: bf17041bf782
Revises: 7866f751b01d
Create Date: 2017-07-23 13:36:31.874179

"""

# revision identifiers, used by Alembic.
revision = 'bf17041bf782'
down_revision = '7866f751b01d'

from alembic import op


def upgrade():
    op.execute("""
        UPDATE profile SET jsonb_settings = jsonb_settings || '{"max_sfw_rating": 10}' WHERE jsonb_settings->'max_sfw_rating' = '20'
    """)


def downgrade():
    raise NotImplementedError

"""Remove thumbnail-legacy links

Revision ID: 652d9ba475f0
Revises: cc2f96b0ba35
Create Date: 2020-03-01 23:17:41.685935

"""

# revision identifiers, used by Alembic.
revision = '652d9ba475f0'
down_revision = 'cc2f96b0ba35'

from alembic import op


def upgrade():
    op.execute("DELETE FROM submission_media_links WHERE link_type = 'thumbnail-legacy'")


def downgrade():
    pass

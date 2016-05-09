"""track oauth consumer app homepages

Provide a way for OAuth2 consumer applications to
register the homepage of their app, giving us
a way to find out where our API's are being used
as well as facilitating the possibility of featuring
3rd party projects.

Revision ID: 3ce027aa9bc4
Revises: abac1922735d
Create Date: 2016-05-09 16:02:48.478539

"""

# revision identifiers, used by Alembic.
revision = '3ce027aa9bc4'
down_revision = 'abac1922735d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('oauth_consumers', sa.Column('homepage', postgresql.TEXT(), nullable=True))


def downgrade():
    op.drop_column('oauth_consumers', 'homepage')

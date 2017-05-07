"""Remove incorrect autoincrements

Revision ID: e50f34d62fd2
Revises: eed15979c8a0
Create Date: 2017-05-06 14:58:50.414577

"""

# revision identifiers, used by Alembic.
revision = 'e50f34d62fd2'
down_revision = 'eed15979c8a0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("DROP SEQUENCE IF EXISTS favorite_targetid_seq CASCADE")
    op.execute("DROP SEQUENCE IF EXISTS views_targetid_seq CASCADE")


def downgrade():
    op.execute("CREATE SEQUENCE favorite_targetid_seq")
    op.execute("CREATE SEQUENCE views_targetid_seq")
    op.execute("ALTER TABLE favorite ALTER COLUMN targetid SET DEFAULT nextval('favorite_targetid_seq')")
    op.execute("ALTER TABLE views ALTER COLUMN targetid SET DEFAULT nextval('views_targetid_seq')")

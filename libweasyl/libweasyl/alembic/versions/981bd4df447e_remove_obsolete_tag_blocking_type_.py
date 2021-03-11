"""Remove obsolete tag blocking type profile config

Revision ID: 981bd4df447e
Revises: 371d1872b404
Create Date: 2021-03-11 04:20:44.425416

"""

# revision identifiers, used by Alembic.
revision = '981bd4df447e'
down_revision = '371d1872b404'

from alembic import op


def upgrade():
    op.execute("UPDATE profile SET config = replace(config, 'l', '') WHERE config ~ 'l'")


def downgrade():
    pass

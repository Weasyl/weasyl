"""Merge moderate rating into general

Revision ID: 25b7048d1a03
Revises: 40c00abab5f9
Create Date: 2017-01-22 17:47:55.239957

"""

# revision identifiers, used by Alembic.
revision = '25b7048d1a03'
down_revision = '40c00abab5f9'

from alembic import op


_RATINGS = {
    "general": 10,
    "moderate": 20,
}


def upgrade():
    op.execute("UPDATE blocktag SET rating = %(general)d WHERE rating = %(moderate)d" % _RATINGS)
    op.execute("UPDATE character SET rating = %(general)d WHERE rating = %(moderate)d" % _RATINGS)
    op.execute("UPDATE journal SET rating = %(general)d WHERE rating = %(moderate)d" % _RATINGS)
    op.execute("UPDATE profile SET config = replace(config, 'm', '') WHERE position('m' in config) != 0")
    op.execute("UPDATE submission SET rating = %(general)d WHERE rating = %(moderate)d" % _RATINGS)


def downgrade():
    raise NotImplementedError

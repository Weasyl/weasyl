# encoding: utf-8

"""Remove “Non-original audio upload” report type

Revision ID: cbe0ea91af79
Revises: c8c088918278
Create Date: 2016-08-11 01:21:10.906138

"""

# revision identifiers, used by Alembic.
revision = 'cbe0ea91af79'
down_revision = 'c8c088918278'

from alembic import op


def upgrade():
    op.execute('UPDATE reportcomment SET violation = 2020 WHERE violation = 2100')


def downgrade():
    raise Exception('Irreversible migration')

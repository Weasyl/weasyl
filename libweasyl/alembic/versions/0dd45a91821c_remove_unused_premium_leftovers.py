"""Remove unused premium leftovers

Revision ID: 0dd45a91821c
Revises: fb60c8528489
Create Date: 2019-09-16 16:44:00.647210

"""

# revision identifiers, used by Alembic.
revision = '0dd45a91821c'
down_revision = 'fb60c8528489'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("UPDATE login SET settings = replace(settings, 'd', '') WHERE settings ~ 'd'")
    op.drop_table('userpremium')
    op.drop_table('premiumpurchase')


def downgrade():
    op.create_table('premiumpurchase',
    sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=254), autoincrement=False, nullable=False),
    sa.Column('terms', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('token', name=u'premiumpurchase_pkey')
    )
    op.create_table('userpremium',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unixtime', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('terms', sa.SMALLINT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['userid'], [u'login.userid'], name=u'userpremium_userid_fkey', onupdate=u'CASCADE', ondelete=u'CASCADE'),
    sa.PrimaryKeyConstraint('userid', name=u'userpremium_pkey')
    )
    op.execute("UPDATE login SET settings = login.settings || 'd' FROM profile WHERE login.settings !~ 'd' AND login.userid = profile.userid AND profile.config ~ 'd'")

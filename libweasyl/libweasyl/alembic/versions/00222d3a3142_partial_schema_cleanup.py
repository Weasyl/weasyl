"""Partial schema cleanup; purges tables: commission, composition, contentview, ignorecontent, loginaddress, logininvite

Revision ID: 00222d3a3142
Revises: 9afc9a45510c
Create Date: 2016-06-30 02:02:03.871635

"""

# revision identifiers, used by Alembic.
revision = '00222d3a3142'
down_revision = '9afc9a45510c'

from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import reflection
import libweasyl


def upgrade():
    """To purge: commission, composition, contentview, ignorecontent, loginaddress, logininvite"""
    
    # The Weasyl latest staff DB doesn't have these tables, so alembic fails to run...
    # Therefore: manually get/check these tables to see if they exist before operating.
    url = context.config.get_main_option("sqlalchemy.url")
    sqa_engine = sa.create_engine(url)
    insp = reflection.Inspector.from_engine(sqa_engine)
    table_names = insp.get_table_names()

    # Drop 'commission' table, if it exists
    if 'commission' in table_names:
        op.drop_table('commission')
    
    # Drop 'composision' table, if it exists
    if 'composition' in table_names:
        op.drop_table('composition')
    
    # Drop 'contentview' table and index, if it exists
    if 'contentview' in table_names:
        op.drop_index('ind_contentview_targetid', table_name='contentview')
        op.drop_table('contentview')
    
    # Drop 'ignorecontent' table and index, if it exists
    if 'ignorecontent' in table_names:
        op.drop_index('ind_ignorecontent_userid', table_name='ignorecontent')
        op.drop_table('ignorecontent')
    
    # Drop 'loginaddress' table, if it exists
    if 'loginaddress' in table_names:
        op.drop_table('loginaddress')
    
    # Drop 'logininvite' table, if it exists
    if 'logininvite' in table_names:
        op.drop_table('logininvite')

def downgrade():
    """To create: commission, composition, contentview, ignorecontent, loginaddress, logininvite"""
    
    # Recreate 'commission'
    op.create_table('commission',
    sa.Column('commishid', sa.String(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('min_amount', sa.Integer(), nullable=False),
    sa.Column('max_amount', sa.Integer(), nullable=True),
    sa.Column('settings', sa.String(), server_default='', nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='commission_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commishid')
    )
    
    # Recreate 'composition'
    op.create_table('composition',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('workid', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='composition_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'workid')
    )
    
    # Recreate 'contentview'
    op.create_table('contentview',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('userid', 'targetid', 'type')
    )
    op.create_index('ind_contentview_targetid', 'contentview', ['targetid'], unique=False)
    
    # Recreate 'ignorecontent'
    op.create_table('ignorecontent',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='ignorecontent_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='ignorecontent_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid')
    )
    op.create_index('ind_ignorecontent_userid', 'ignorecontent', ['userid'], unique=False)
    
    # Recreate 'loginaddress'
    op.create_table('loginaddress',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='loginaddress_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'address')
    )
    
    # Recreate 'logininvite'
    op.create_table('logininvite',
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('email')
    )


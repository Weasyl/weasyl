"""Squash revisions for publication

Revision ID: abac1922735d
Revises: None
Create Date: 2016-05-26 23:09:36.027672

"""

# revision identifiers, used by Alembic.
revision = 'abac1922735d'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import libweasyl


closure_reason_enum = postgresql.ENUM(
    'legacy',
    'action-taken',
    'no-action-taken',
    'invalid',
    name='report_closure_reason')


def upgrade():
    op.create_table('contentview',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('userid', 'targetid', 'type')
    )
    op.create_index('ind_contentview_targetid', 'contentview', ['targetid'], unique=False)
    op.create_table('cron_runs',
    sa.Column('last_run', postgresql.TIMESTAMP(), nullable=False)
    )
    op.create_table('login',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('login_name', sa.String(length=40), nullable=False),
    sa.Column('last_login', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('email', sa.String(length=100), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('userid'),
    sa.UniqueConstraint('login_name')
    )
    op.create_index('ind_login_login_name', 'login', ['login_name'], unique=False)
    op.create_table('logincreate',
    sa.Column('token', sa.String(length=100), nullable=False),
    sa.Column('username', sa.String(length=40), nullable=False),
    sa.Column('login_name', sa.String(length=40), nullable=False),
    sa.Column('hashpass', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('birthday', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.PrimaryKeyConstraint('token'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('login_name')
    )
    op.create_table('logininvite',
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('email')
    )
    op.create_table('media',
    sa.Column('mediaid', sa.Integer(), nullable=False),
    sa.Column('media_type', sa.String(length=32), nullable=False),
    sa.Column('file_type', sa.String(length=8), nullable=False),
    sa.Column('attributes', libweasyl.models.helpers.JSONValuesColumn(), server_default=sa.text("''::hstore"), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('mediaid')
    )
    op.create_table('premiumpurchase',
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('terms', sa.SMALLINT(), nullable=False),
    sa.PrimaryKeyConstraint('token')
    )
    op.create_table('searchtag',
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('tagid'),
    sa.UniqueConstraint('title')
    )
    op.create_index('ind_searchtag_tagid', 'searchtag', ['tagid'], unique=False)
    op.create_table('views',
    sa.Column('viewer', sa.String(length=127), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('viewer', 'targetid', 'type')
    )
    op.create_table('ads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner', sa.Text(), nullable=False),
    sa.Column('link_target', sa.Text(), nullable=False),
    sa.Column('file', sa.Integer(), nullable=False),
    sa.Column('start', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('end', postgresql.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['file'], ['media.mediaid'], name='ads_file_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ind_ads_end', 'ads', ['end'], unique=False)
    op.create_table('api_tokens',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='api_tokens_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'token')
    )
    op.create_table('authbcrypt',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('hashsum', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='authbcrypt_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('blocktag',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='blocktag_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='blocktag_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'tagid')
    )
    op.create_index('ind_blocktag_userid', 'blocktag', ['userid'], unique=False)
    op.create_table('character',
    sa.Column('charid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('char_name', sa.String(length=100), server_default='', nullable=False),
    sa.Column('age', sa.String(length=100), server_default='', nullable=False),
    sa.Column('gender', sa.String(length=100), server_default='', nullable=False),
    sa.Column('height', sa.String(length=100), server_default='', nullable=False),
    sa.Column('weight', sa.String(length=100), server_default='', nullable=False),
    sa.Column('species', sa.String(length=100), server_default='', nullable=False),
    sa.Column('content', sa.Text(), server_default=sa.text("''::text"), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('page_views', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='character_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('charid')
    )
    op.create_index('ind_character_userid', 'character', ['userid'], unique=False)
    op.create_table('commishclass',
    sa.Column('classid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='commishclass_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('classid', 'userid')
    )
    op.create_index('ind_commishclass_userid', 'commishclass', ['userid'], unique=False)
    op.create_index('ind_userid_title', 'commishclass', ['userid', 'title'], unique=True)
    op.create_table('commishdesc',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='commishdesc_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('commishprice',
    sa.Column('priceid', sa.Integer(), nullable=False),
    sa.Column('classid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('amount_min', sa.Integer(), nullable=False),
    sa.Column('amount_max', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='commishprice_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('priceid', 'classid', 'userid')
    )
    op.create_index('ind_classid_userid_title', 'commishprice', ['classid', 'userid', 'title'], unique=True)
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
    op.create_table('composition',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('workid', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='composition_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'workid')
    )
    op.create_table('disk_media',
    sa.Column('mediaid', sa.Integer(), nullable=False),
    sa.Column('file_path', sa.String(length=255), nullable=False),
    sa.Column('file_url', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['mediaid'], ['media.mediaid'], name='disk_media_mediaid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('mediaid')
    )
    op.create_table('emailverify',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='emailverify_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid'),
    sa.UniqueConstraint('email')
    )
    op.create_table('favorite',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=5), server_default='', nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='favorite_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'targetid', 'type')
    )
    op.create_index('ind_favorite_type_targetid', 'favorite', ['type', 'targetid'], unique=False)
    op.create_index('ind_favorite_userid', 'favorite', ['userid'], unique=False)
    op.create_table('folder',
    sa.Column('folderid', sa.Integer(), nullable=False),
    sa.Column('parentid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='folder_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('folderid')
    )
    op.create_index('ind_folder_userid', 'folder', ['userid'], unique=False)
    op.create_table('forgotpassword',
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('token', sa.String(length=100), nullable=False),
    sa.Column('set_time', sa.Integer(), nullable=False),
    sa.Column('link_time', sa.Integer(), server_default='0', nullable=False),
    sa.Column('address', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='forgotpassword_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token'),
    sa.UniqueConstraint('userid')
    )
    op.create_table('frienduser',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='p', nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), server_default=sa.text("(date_part('epoch'::text, now()) - (18000)::double precision)"), nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='frienduser_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='frienduser_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid')
    )
    op.create_index('ind_frienduser_otherid', 'frienduser', ['otherid'], unique=False)
    op.create_index('ind_frienduser_userid', 'frienduser', ['userid'], unique=False)
    op.create_table('ignorecontent',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='ignorecontent_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='ignorecontent_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid')
    )
    op.create_index('ind_ignorecontent_userid', 'ignorecontent', ['userid'], unique=False)
    op.create_table('ignoreuser',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='ignoreuser_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='ignoreuser_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid')
    )
    op.create_index('ind_ignoreuser_userid', 'ignoreuser', ['userid'], unique=False)
    op.create_table('journal',
    sa.Column('journalid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('page_views', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='journal_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('journalid')
    )
    op.create_index('ind_journal_userid', 'journal', ['userid'], unique=False)
    op.create_table('loginaddress',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='loginaddress_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'address')
    )
    op.create_table('media_media_links',
    sa.Column('linkid', sa.Integer(), nullable=False),
    sa.Column('described_with_id', sa.Integer(), nullable=False),
    sa.Column('describee_id', sa.Integer(), nullable=False),
    sa.Column('link_type', sa.String(length=32), nullable=False),
    sa.Column('attributes', libweasyl.models.helpers.JSONValuesColumn(), server_default=sa.text("''::hstore"), nullable=False),
    sa.ForeignKeyConstraint(['described_with_id'], ['media.mediaid'], name='media_media_links_described_with_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['describee_id'], ['media.mediaid'], name='media_media_links_describee_id_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('linkid')
    )
    op.create_index('ind_media_media_links_described_with_id', 'media_media_links', ['described_with_id'], unique=False)
    op.create_index('ind_media_media_links_describee_id', 'media_media_links', ['describee_id'], unique=False)
    op.create_index('ind_media_media_links_submitid', 'media_media_links', ['describee_id'], unique=False)
    op.create_table('message',
    sa.Column('noteid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('otherid', sa.Integer(), nullable=True),
    sa.Column('user_folder', sa.Integer(), server_default='0', nullable=False),
    sa.Column('other_folder', sa.Integer(), server_default='0', nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='u', nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='message_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='message_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('noteid')
    )
    op.create_index('ind_message_otherid', 'message', ['otherid'], unique=False)
    op.create_index('ind_message_userid', 'message', ['userid'], unique=False)
    op.create_table('oauth_consumers',
    sa.Column('clientid', sa.String(length=32), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('ownerid', sa.Integer(), nullable=False),
    sa.Column('grant_type', sa.String(length=32), nullable=False),
    sa.Column('response_type', sa.String(length=32), nullable=False),
    sa.Column('scopes', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('redirect_uris', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('client_secret', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['ownerid'], ['login.userid'], name='oauth_consumers_owner_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('clientid')
    )
    op.create_table('permaban',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='permaban_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('profile',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=40), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=False),
    sa.Column('catchphrase', sa.String(length=200), server_default='', nullable=False),
    sa.Column('artist_type', sa.String(length=100), server_default='', nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('profile_text', sa.Text(), server_default='', nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='ccci', nullable=False),
    sa.Column('stream_url', sa.String(length=500), server_default='', nullable=False),
    sa.Column('page_views', sa.Integer(), server_default='0', nullable=False),
    sa.Column('config', sa.String(length=50), server_default='', nullable=False),
    sa.Column('jsonb_settings', postgresql.JSONB(), nullable=True),
    sa.Column('stream_time', sa.Integer(), nullable=True),
    sa.Column('stream_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='profile_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid'),
    sa.UniqueConstraint('username')
    )
    op.create_table('sessions',
    sa.Column('sessionid', sa.String(length=64), nullable=False),
    sa.Column('created_at', libweasyl.models.helpers.ArrowColumn(), server_default=sa.text('now()'), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('csrf_token', sa.String(length=64), nullable=True),
    sa.Column('additional_data', libweasyl.models.helpers.JSONValuesColumn(), server_default=sa.text("''::hstore"), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='sessions_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('sessionid')
    )
    op.create_index('ind_sessions_created_at', 'sessions', ['created_at'], unique=False)
    op.create_table('siteupdate',
    sa.Column('updateid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='siteupdate_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('updateid')
    )
    op.create_table('suspension',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('release', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='suspension_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('user_links',
    sa.Column('linkid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('link_type', sa.String(length=64), nullable=False),
    sa.Column('link_value', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_links_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('linkid')
    )
    op.create_index('ind_user_links_userid', 'user_links', ['userid'], unique=False)
    op.create_table('user_media_links',
    sa.Column('linkid', sa.Integer(), nullable=False),
    sa.Column('mediaid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('link_type', sa.String(length=32), nullable=False),
    sa.Column('attributes', libweasyl.models.helpers.JSONValuesColumn(), server_default=sa.text("''::hstore"), nullable=False),
    sa.ForeignKeyConstraint(['mediaid'], ['media.mediaid'], name='user_media_links_mediaid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_media_links_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('linkid')
    )
    op.create_index('ind_user_media_links_mediaid', 'user_media_links', ['mediaid'], unique=False)
    op.create_index('ind_user_media_links_submitid', 'user_media_links', ['userid'], unique=False)
    op.create_index('ind_user_media_links_userid', 'user_media_links', ['userid'], unique=False)
    op.create_table('user_streams',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('start_time', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('end_time', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_streams_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_index('ind_user_streams_end', 'user_streams', ['end_time'], unique=False)
    op.create_index('ind_user_streams_end_time', 'user_streams', ['end_time'], unique=False)
    op.create_table('user_timezones',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('timezone', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='user_timezones_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('useralias',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('alias_name', sa.String(length=40), nullable=False),
    sa.Column('settings', sa.String(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='useralias_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'alias_name')
    )
    op.create_table('userinfo',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('birthday', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('gender', sa.String(length=25), server_default='', nullable=False),
    sa.Column('country', sa.String(length=50), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='userinfo_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('userpremium',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('terms', sa.SMALLINT(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='userpremium_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('userstats',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('page_views', sa.Integer(), server_default='0', nullable=False),
    sa.Column('submit_views', sa.Integer(), server_default='0', nullable=False),
    sa.Column('followers', sa.Integer(), server_default='0', nullable=False),
    sa.Column('faved_works', sa.Integer(), server_default='0', nullable=False),
    sa.Column('journals', sa.Integer(), server_default='0', nullable=False),
    sa.Column('submits', sa.Integer(), server_default='0', nullable=False),
    sa.Column('characters', sa.Integer(), server_default='0', nullable=False),
    sa.Column('collects', sa.Integer(), server_default='0', nullable=False),
    sa.Column('faves', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='userstats_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_table('watchuser',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(length=20), nullable=False),
    sa.Column('unixtime', sa.Integer(), server_default=sa.text("(date_part('epoch'::text, now()) - (18000)::double precision)"), nullable=False),
    sa.ForeignKeyConstraint(['otherid'], ['login.userid'], name='watchuser_otherid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='watchuser_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'otherid')
    )
    op.create_index('ind_watchuser_otherid', 'watchuser', ['otherid'], unique=False)
    op.create_index('ind_watchuser_otherid_settings', 'watchuser', ['otherid', 'settings'], unique=False)
    op.create_index('ind_watchuser_settings', 'watchuser', ['settings'], unique=False)
    op.create_index('ind_watchuser_userid', 'watchuser', ['userid'], unique=False)
    op.create_index('ind_watchuser_userid_settings', 'watchuser', ['userid', 'settings'], unique=False)
    op.create_table('welcome',
    sa.Column('welcomeid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('otherid', sa.Integer(), nullable=False),
    sa.Column('referid', sa.Integer(), server_default='0', nullable=False),
    sa.Column('targetid', sa.Integer(), server_default='0', nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('deleted', libweasyl.models.helpers.ArrowColumn(), nullable=True),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='welcome_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('welcomeid')
    )
    op.create_index('ind_welcome_otherid', 'welcome', ['otherid'], unique=False)
    op.create_index('ind_welcome_referid', 'welcome', ['referid'], unique=False)
    op.create_index('ind_welcome_targetid', 'welcome', ['targetid'], unique=False)
    op.create_index('ind_welcome_type', 'welcome', ['type'], unique=False)
    op.create_index('ind_welcome_unixtime', 'welcome', ['unixtime'], unique=False)
    op.create_index('ind_welcome_userid_type', 'welcome', ['userid', 'type'], unique=False)
    op.create_table('welcomecount',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('journal', sa.Integer(), server_default='0', nullable=False),
    sa.Column('submit', sa.Integer(), server_default='0', nullable=False),
    sa.Column('notify', sa.Integer(), server_default='0', nullable=False),
    sa.Column('comment', sa.Integer(), server_default='0', nullable=False),
    sa.Column('note', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='welcomecount_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid')
    )
    op.create_index('ind_welcomecount_userid', 'welcomecount', ['userid'], unique=False)
    op.create_table('charcomment',
    sa.Column('commentid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('targetid', sa.Integer(), nullable=True),
    sa.Column('parentid', sa.Integer(), server_default='0', nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('indent', sa.Integer(), server_default='0', nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('hidden_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['hidden_by'], ['login.userid'], name='charcomment_hidden_by_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['targetid'], ['character.charid'], name='charcomment_targetid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='charcomment_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commentid')
    )
    op.create_index('ind_charcomment_targetid', 'charcomment', ['targetid'], unique=False)
    op.create_table('journalcomment',
    sa.Column('commentid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('targetid', sa.Integer(), nullable=True),
    sa.Column('parentid', sa.Integer(), server_default='0', nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('indent', sa.Integer(), server_default='0', nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('hidden_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['hidden_by'], ['login.userid'], name='journalcomment_hidden_by_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['targetid'], ['journal.journalid'], name='journalcomment_targetid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='journalcomment_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commentid')
    )
    op.create_index('ind_journalcomment_settings', 'journalcomment', ['settings'], unique=False)
    op.create_index('ind_journalcomment_targetid', 'journalcomment', ['targetid'], unique=False)
    op.create_index('ind_journalcomment_targetid_settings', 'journalcomment', ['targetid', 'settings'], unique=False)
    op.create_table('oauth_bearer_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('clientid', sa.String(length=32), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('scopes', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('access_token', sa.String(length=64), nullable=False),
    sa.Column('refresh_token', sa.String(length=64), nullable=False),
    sa.Column('expires_at', libweasyl.models.helpers.ArrowColumn(), nullable=False),
    sa.ForeignKeyConstraint(['clientid'], ['oauth_consumers.clientid'], name='oauth_bearer_tokens_clientid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='oauth_bearer_tokens_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('access_token'),
    sa.UniqueConstraint('refresh_token')
    )
    op.create_table('searchmapchar',
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapchar_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['targetid'], ['character.charid'], name='searchmapchar_targetid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('tagid', 'targetid')
    )
    op.create_index('ind_searchmapchar_tagid', 'searchmapchar', ['tagid'], unique=False)
    op.create_index('ind_searchmapchar_targetid', 'searchmapchar', ['targetid'], unique=False)
    op.create_table('searchmapjournal',
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapjournal_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['targetid'], ['journal.journalid'], name='searchmapjournal_targetid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('tagid', 'targetid')
    )
    op.create_index('ind_searchmapjournal_tagid', 'searchmapjournal', ['tagid'], unique=False)
    op.create_index('ind_searchmapjournal_targetid', 'searchmapjournal', ['targetid'], unique=False)
    op.create_table('submission',
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('folderid', sa.Integer(), nullable=True),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('subtype', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('page_views', sa.Integer(), server_default='0', nullable=False),
    sa.Column('sorttime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('fave_count', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['folderid'], ['folder.folderid'], name='submission_folderid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='submission_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('submitid')
    )
    op.create_index('ind_submission_folderid', 'submission', ['folderid'], unique=False)
    op.create_index('ind_submission_userid', 'submission', ['userid'], unique=False)
    op.create_index('ind_submission_userid_folderid', 'submission', ['userid', 'folderid'], unique=False)
    op.create_index('ind_submission_userid_unixtime', 'submission', ['userid', sa.text('unixtime DESC')], unique=False)
    op.create_table('collection',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='p', nullable=False),
    sa.ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='collection_submitid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='collection_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('userid', 'submitid')
    )
    op.create_index('ind_collection_userid', 'collection', ['userid'], unique=False)
    op.create_table('comments',
    sa.Column('commentid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('target_user', sa.Integer(), nullable=True),
    sa.Column('target_sub', sa.Integer(), nullable=True),
    sa.Column('parentid', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('indent', sa.Integer(), server_default='0', nullable=False),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('hidden_by', sa.Integer(), nullable=True),
    sa.CheckConstraint('(target_user IS NOT NULL) != (target_sub IS NOT NULL)', name='comments_target_check'),
    sa.ForeignKeyConstraint(['hidden_by'], ['login.userid'], name='comments_hidden_by_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parentid'], ['comments.commentid'], name='comments_parentid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_sub'], ['submission.submitid'], name='comments_target_sub_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_user'], ['login.userid'], name='comments_target_user_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='comments_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commentid')
    )
    op.create_index(op.f('ix_comments_target_sub'), 'comments', ['target_sub'], unique=False)
    op.create_index(op.f('ix_comments_target_user'), 'comments', ['target_user'], unique=False)
    op.create_table('google_doc_embeds',
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('embed_url', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='google_doc_embeds_submitid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('submitid')
    )
    op.create_table('searchmapsubmit',
    sa.Column('tagid', sa.Integer(), nullable=False),
    sa.Column('targetid', sa.Integer(), nullable=False),
    sa.Column('settings', sa.String(), server_default='', nullable=False),
    sa.ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapsubmit_tagid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['targetid'], ['submission.submitid'], name='searchmapsubmit_targetid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('tagid', 'targetid')
    )
    op.create_index('ind_searchmapsubmit_tagid', 'searchmapsubmit', ['tagid'], unique=False)
    op.create_index('ind_searchmapsubmit_targetid', 'searchmapsubmit', ['targetid'], unique=False)
    op.create_table('submission_media_links',
    sa.Column('linkid', sa.Integer(), nullable=False),
    sa.Column('mediaid', sa.Integer(), nullable=False),
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('link_type', sa.String(length=32), nullable=False),
    sa.Column('attributes', libweasyl.models.helpers.JSONValuesColumn(), server_default=sa.text("''::hstore"), nullable=False),
    sa.ForeignKeyConstraint(['mediaid'], ['media.mediaid'], name='submission_media_links_mediaid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='submission_media_links_submitid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('linkid')
    )
    op.create_index('ind_submission_media_links_mediaid', 'submission_media_links', ['mediaid'], unique=False)
    op.create_index('ind_submission_media_links_submitid', 'submission_media_links', ['submitid'], unique=False)
    op.create_table('tag_updates',
    sa.Column('updateid', sa.Integer(), nullable=False),
    sa.Column('submitid', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('added', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('removed', postgresql.ARRAY(sa.Text()), nullable=True),
    sa.Column('updated_at', sa.Integer(), server_default=sa.text("(date_part('epoch'::text, now()) - (18000)::double precision)"), nullable=False),
    sa.ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='tag_updates_submitid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='tag_updates_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('updateid')
    )
    op.create_table('report',
    sa.Column('target_user', sa.Integer(), nullable=True),
    sa.Column('target_sub', sa.Integer(), nullable=True),
    sa.Column('target_char', sa.Integer(), nullable=True),
    sa.Column('target_journal', sa.Integer(), nullable=True),
    sa.Column('target_comment', sa.Integer(), nullable=True),
    sa.Column('opened_at', libweasyl.models.helpers.ArrowColumn(), nullable=False),
    sa.Column('urgency', sa.Integer(), nullable=False),
    sa.Column('closerid', sa.Integer(), nullable=True),
    sa.Column('settings', sa.String(length=20), server_default='', nullable=False),
    sa.Column('reportid', sa.Integer(), nullable=False),
    sa.Column('closed_at', libweasyl.models.helpers.ArrowColumn(), nullable=True),
    sa.Column('closure_reason', closure_reason_enum, nullable=True),
    sa.Column('closure_explanation', sa.Text(), nullable=True),
    sa.CheckConstraint('((closed_at IS NOT NULL)::int + (closure_reason IS NOT NULL)::int   + (closure_explanation IS NOT NULL)::int) IN (0, 3)', name='report_closure_check'),
    sa.CheckConstraint('((target_user IS NOT NULL)::int + (target_sub IS NOT NULL)::int   + (target_char IS NOT NULL)::int + (target_journal IS NOT NULL)::int   + (target_comment IS NOT NULL)::int) = 1', name='report_target_check'),
    sa.ForeignKeyConstraint(['closerid'], ['login.userid'], name='report_closerid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_char'], ['character.charid'], name='report_target_char_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_comment'], ['comments.commentid'], name='report_target_comment_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_journal'], ['journal.journalid'], name='report_target_journal_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_sub'], ['submission.submitid'], name='report_target_sub_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_user'], ['login.userid'], name='report_target_user_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('reportid')
    )
    op.create_table('reportcomment',
    sa.Column('violation', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('unixtime', libweasyl.models.helpers.WeasylTimestampColumn(), nullable=False),
    sa.Column('content', sa.String(length=2000), server_default='', nullable=False),
    sa.Column('commentid', sa.Integer(), nullable=False),
    sa.Column('reportid', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['reportid'], ['report.reportid'], name='reportcomment_reportid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['userid'], ['login.userid'], name='reportcomment_userid_fkey', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('commentid')
    )


def downgrade():
    op.drop_table('reportcomment')
    op.drop_table('report')
    op.drop_table('tag_updates')
    op.drop_index('ind_submission_media_links_submitid', table_name='submission_media_links')
    op.drop_index('ind_submission_media_links_mediaid', table_name='submission_media_links')
    op.drop_table('submission_media_links')
    op.drop_index('ind_searchmapsubmit_targetid', table_name='searchmapsubmit')
    op.drop_index('ind_searchmapsubmit_tagid', table_name='searchmapsubmit')
    op.drop_table('searchmapsubmit')
    op.drop_table('google_doc_embeds')
    op.drop_index(op.f('ix_comments_target_user'), table_name='comments')
    op.drop_index(op.f('ix_comments_target_sub'), table_name='comments')
    op.drop_table('comments')
    op.drop_index('ind_collection_userid', table_name='collection')
    op.drop_table('collection')
    op.drop_index('ind_submission_userid_unixtime', table_name='submission')
    op.drop_index('ind_submission_userid_folderid', table_name='submission')
    op.drop_index('ind_submission_userid', table_name='submission')
    op.drop_index('ind_submission_folderid', table_name='submission')
    op.drop_table('submission')
    op.drop_index('ind_searchmapjournal_targetid', table_name='searchmapjournal')
    op.drop_index('ind_searchmapjournal_tagid', table_name='searchmapjournal')
    op.drop_table('searchmapjournal')
    op.drop_index('ind_searchmapchar_targetid', table_name='searchmapchar')
    op.drop_index('ind_searchmapchar_tagid', table_name='searchmapchar')
    op.drop_table('searchmapchar')
    op.drop_table('oauth_bearer_tokens')
    op.drop_index('ind_journalcomment_targetid_settings', table_name='journalcomment')
    op.drop_index('ind_journalcomment_targetid', table_name='journalcomment')
    op.drop_index('ind_journalcomment_settings', table_name='journalcomment')
    op.drop_table('journalcomment')
    op.drop_index('ind_charcomment_targetid', table_name='charcomment')
    op.drop_table('charcomment')
    op.drop_index('ind_welcomecount_userid', table_name='welcomecount')
    op.drop_table('welcomecount')
    op.drop_index('ind_welcome_userid_type', table_name='welcome')
    op.drop_index('ind_welcome_unixtime', table_name='welcome')
    op.drop_index('ind_welcome_type', table_name='welcome')
    op.drop_index('ind_welcome_targetid', table_name='welcome')
    op.drop_index('ind_welcome_referid', table_name='welcome')
    op.drop_index('ind_welcome_otherid', table_name='welcome')
    op.drop_table('welcome')
    op.drop_index('ind_watchuser_userid_settings', table_name='watchuser')
    op.drop_index('ind_watchuser_userid', table_name='watchuser')
    op.drop_index('ind_watchuser_settings', table_name='watchuser')
    op.drop_index('ind_watchuser_otherid_settings', table_name='watchuser')
    op.drop_index('ind_watchuser_otherid', table_name='watchuser')
    op.drop_table('watchuser')
    op.drop_table('userstats')
    op.drop_table('userpremium')
    op.drop_table('userinfo')
    op.drop_table('useralias')
    op.drop_table('user_timezones')
    op.drop_index('ind_user_streams_end_time', table_name='user_streams')
    op.drop_index('ind_user_streams_end', table_name='user_streams')
    op.drop_table('user_streams')
    op.drop_index('ind_user_media_links_userid', table_name='user_media_links')
    op.drop_index('ind_user_media_links_submitid', table_name='user_media_links')
    op.drop_index('ind_user_media_links_mediaid', table_name='user_media_links')
    op.drop_table('user_media_links')
    op.drop_index('ind_user_links_userid', table_name='user_links')
    op.drop_table('user_links')
    op.drop_table('suspension')
    op.drop_table('siteupdate')
    op.drop_index('ind_sessions_created_at', table_name='sessions')
    op.drop_table('sessions')
    op.drop_table('profile')
    op.drop_table('permaban')
    op.drop_table('oauth_consumers')
    op.drop_index('ind_message_userid', table_name='message')
    op.drop_index('ind_message_otherid', table_name='message')
    op.drop_table('message')
    op.drop_index('ind_media_media_links_submitid', table_name='media_media_links')
    op.drop_index('ind_media_media_links_describee_id', table_name='media_media_links')
    op.drop_index('ind_media_media_links_described_with_id', table_name='media_media_links')
    op.drop_table('media_media_links')
    op.drop_table('loginaddress')
    op.drop_index('ind_journal_userid', table_name='journal')
    op.drop_table('journal')
    op.drop_index('ind_ignoreuser_userid', table_name='ignoreuser')
    op.drop_table('ignoreuser')
    op.drop_index('ind_ignorecontent_userid', table_name='ignorecontent')
    op.drop_table('ignorecontent')
    op.drop_index('ind_frienduser_userid', table_name='frienduser')
    op.drop_index('ind_frienduser_otherid', table_name='frienduser')
    op.drop_table('frienduser')
    op.drop_table('forgotpassword')
    op.drop_index('ind_folder_userid', table_name='folder')
    op.drop_table('folder')
    op.drop_index('ind_favorite_userid', table_name='favorite')
    op.drop_index('ind_favorite_type_targetid', table_name='favorite')
    op.drop_table('favorite')
    op.drop_table('emailverify')
    op.drop_table('disk_media')
    op.drop_table('composition')
    op.drop_table('commission')
    op.drop_index('ind_classid_userid_title', table_name='commishprice')
    op.drop_table('commishprice')
    op.drop_table('commishdesc')
    op.drop_index('ind_userid_title', table_name='commishclass')
    op.drop_index('ind_commishclass_userid', table_name='commishclass')
    op.drop_table('commishclass')
    op.drop_index('ind_character_userid', table_name='character')
    op.drop_table('character')
    op.drop_index('ind_blocktag_userid', table_name='blocktag')
    op.drop_table('blocktag')
    op.drop_table('authbcrypt')
    op.drop_table('api_tokens')
    op.drop_index('ind_ads_end', table_name='ads')
    op.drop_table('ads')
    op.drop_table('views')
    op.drop_index('ind_searchtag_tagid', table_name='searchtag')
    op.drop_table('searchtag')
    op.drop_table('premiumpurchase')
    op.drop_table('media')
    op.drop_table('logininvite')
    op.drop_table('logincreate')
    op.drop_index('ind_login_login_name', table_name='login')
    op.drop_table('login')
    op.drop_table('cron_runs')
    op.drop_index('ind_contentview_targetid', table_name='contentview')
    op.drop_table('contentview')

from sqlalchemy import (
    MetaData, Table, Column, CheckConstraint, UniqueConstraint, Index,
    BigInteger, Boolean, Date, DateTime, Integer, String, Text, func, text)
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, ENUM, JSONB, TIMESTAMP
from sqlalchemy.schema import ForeignKey as _ForeignKey
from sqlalchemy.schema import ForeignKeyConstraint as _ForeignKeyConstraint
from sqlalchemy.schema import PrimaryKeyConstraint

from libweasyl.models.helpers import (
    ArrowColumn, CharSettingsColumn, JSONValuesColumn, RatingColumn, WeasylTimestampColumn)
from libweasyl import constants
from weasyl.users import USERNAME_MAX_LENGTH


metadata = MetaData()

Permissions = ENUM(
    "nobody",
    "friends",
    "everyone",
    name="permissions",
    metadata=metadata,
)

ProfileStatus = ENUM(
    "exclude",
    "closed",
    "filled",
    "sometimes",
    "open",
    name="profile_status",
    metadata=metadata,
)

Rating = ENUM(
    "general",
    "mature",
    "explicit",
    name="rating",
    metadata=metadata,
)


# Make all foreign keys deferrable by default.
def ForeignKey(*args, **kwargs) -> _ForeignKey:
    return _ForeignKey(*args, **kwargs, deferrable=True)


def ForeignKeyConstraint(*args, **kwargs) -> _ForeignKeyConstraint:
    return _ForeignKeyConstraint(*args, **kwargs, deferrable=True)


def cascading_fkey(*args, **kwargs):
    return ForeignKeyConstraint(*args, onupdate='CASCADE', ondelete='CASCADE', **kwargs)


api_tokens = Table(
    'api_tokens', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('token', String(length=64), primary_key=True, nullable=False),
    Column('description', String()),
    cascading_fkey(['userid'], ['login.userid'], name='api_tokens_userid_fkey'),
)


authbcrypt = Table(
    'authbcrypt', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('hashsum', String(length=100), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='authbcrypt_userid_fkey'),
)


blocktag = Table(
    'blocktag', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('rating', RatingColumn, nullable=False),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='blocktag_tagid_fkey'),
    cascading_fkey(['userid'], ['login.userid'], name='blocktag_userid_fkey'),
)

Index('ind_blocktag_userid', blocktag.c.userid)


charcomment = Table(
    'charcomment', metadata,
    Column('commentid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('targetid', Integer(), nullable=False),
    Column('parentid', Integer(), nullable=False, server_default='0'),
    Column('content', String(length=10000), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('settings', String(length=20), nullable=False, server_default=''),
    Column('hidden_by', Integer(), nullable=True),
    ForeignKeyConstraint(['targetid'], ['character.charid'], name='charcomment_targetid_fkey'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='charcomment_userid_fkey'),
    ForeignKeyConstraint(
        ['hidden_by'],
        ['login.userid'],
        name='charcomment_hidden_by_fkey',
        ondelete='SET NULL',
    ),
)

Index('ind_charcomment_targetid_commentid', charcomment.c.targetid, charcomment.c.commentid)


collection = Table(
    'collection', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('submitid', Integer(), primary_key=True, nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('settings', String(length=20), nullable=False, server_default='p'),
    cascading_fkey(['userid'], ['login.userid'], name='collection_userid_fkey'),
    ForeignKeyConstraint(['submitid'], ['submission.submitid'], name='collection_submitid_fkey'),
)

Index('ind_collection_userid', collection.c.userid)


comments = Table(
    'comments', metadata,
    Column('commentid', Integer(), primary_key=True),
    Column('userid', Integer(), nullable=False),
    Column('target_user', Integer(), nullable=True),
    Column('target_sub', Integer(), nullable=True),
    Column('parentid', Integer(), nullable=True),
    Column('content', Text(), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('settings', CharSettingsColumn({
        'h': 'hidden',
        's': 'staff-note',
    }, length=20), nullable=False, server_default=''),
    Column('hidden_by', Integer(), nullable=True),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='comments_userid_fkey'),
    ForeignKeyConstraint(['target_user'], ['login.userid'], name='comments_target_user_fkey'),
    ForeignKeyConstraint(['target_sub'], ['submission.submitid'], name='comments_target_sub_fkey'),
    ForeignKeyConstraint(['parentid'], ['comments.commentid'], name='comments_parentid_fkey'),
    ForeignKeyConstraint(
        ['hidden_by'],
        ['login.userid'],
        name='comments_hidden_by_fkey',
        ondelete='SET NULL',
    ),
    CheckConstraint('(target_user IS NOT NULL) != (target_sub IS NOT NULL)', name='comments_target_check'),
)

Index('ind_comments_target_user_commentid', comments.c.target_user, comments.c.commentid, postgresql_where=comments.c.target_user != None)
Index('ind_comments_target_sub_commentid', comments.c.target_sub, comments.c.commentid, postgresql_where=comments.c.target_sub != None)


commishclass = Table(
    'commishclass', metadata,
    Column('classid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('title', String(length=100), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='commishclass_userid_fkey'),
)

Index('ind_userid_title', commishclass.c.userid, commishclass.c.title, unique=True)
Index('ind_commishclass_userid', commishclass.c.userid)


commishdesc = Table(
    'commishdesc', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('content', String(length=20000), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='commishdesc_userid_fkey'),
)


commishprice = Table(
    'commishprice', metadata,
    Column('priceid', Integer(), primary_key=True, nullable=False),
    Column('classid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('title', String(length=500), nullable=False),
    Column('amount_min', Integer(), nullable=False),
    Column('amount_max', Integer(), nullable=False),
    Column('settings', String(length=20), nullable=False, server_default=''),
    cascading_fkey(['userid'], ['login.userid'], name='commishprice_userid_fkey'),
)

Index('ind_classid_userid_title', commishprice.c.classid, commishprice.c.userid, commishprice.c.title, unique=True)


emailverify = Table(
    'emailverify', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('email', String(length=100), nullable=False, unique=True),
    Column('createtimestamp', DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column('token', String(length=100), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='emailverify_userid_fkey'),
)

Index('ind_emailverify_token', emailverify.c.token)


favorite = Table(
    'favorite', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False, autoincrement=False),
    Column('type', String(length=5), primary_key=True, nullable=False, server_default=''),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='favorite_userid_fkey'),
)

Index('ind_favorite_userid', favorite.c.userid)
Index('ind_favorite_type_targetid', favorite.c.type, favorite.c.targetid)
Index('ind_favorite_userid_type_unixtime', favorite.c.userid, favorite.c.type, favorite.c.unixtime)


folder = Table(
    'folder', metadata,
    Column('folderid', Integer(), primary_key=True, nullable=False),
    Column('parentid', Integer(), nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('title', String(length=100), nullable=False),
    Column('settings', CharSettingsColumn({
        'h': 'hidden',
        'n': 'no-notifications',
        'u': 'profile-filter',
        'm': 'index-filter',
        'f': 'featured-filter',
    }, length=20), nullable=False, server_default=''),
    cascading_fkey(['userid'], ['login.userid'], name='folder_userid_fkey'),
)

Index('ind_folder_userid', folder.c.userid)


forgotpassword = Table(
    'forgotpassword', metadata,
    Column('token_sha256', BYTEA(), primary_key=True, nullable=False),
    Column('email', String(length=254), nullable=False),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
)

Index('ind_forgotpassword_created_at', forgotpassword.c.created_at)


frienduser = Table(
    'frienduser', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('otherid', Integer(), primary_key=True, nullable=False),
    Column('settings', CharSettingsColumn({
        'p': 'pending',
    }, length=20), nullable=False, server_default='p'),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),

    # Initially: write-only
    # Future migration: `SET accepted_at = created_at WHERE settings !~ 'p'`
    # After migration: determines whether the friend request has been accepted (`settings` column can then be dropped)
    Column('accepted_at', TIMESTAMP(timezone=True)),

    cascading_fkey(['otherid'], ['login.userid'], name='frienduser_otherid_fkey'),
    cascading_fkey(['userid'], ['login.userid'], name='frienduser_userid_fkey'),
    CheckConstraint("settings IN ('', 'p')", name='frienduser_settings_check'),
    CheckConstraint("accepted_at IS NULL OR settings = ''", name='frienduser_accepted_at_check'),
)

Index('ind_frienduser_otherid', frienduser.c.otherid)

# A unique index on `(min(a, b), a ^ b)` enforces that each unordered pair of users has at most one row in `frienduser`.
Index(
    'ind_frienduser_uniq',
    func.least(frienduser.c.userid, frienduser.c.otherid),
    frienduser.c.userid.op('#')(frienduser.c.otherid),
    unique=True,
)


character = Table(
    'character', metadata,
    Column('charid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('char_name', String(length=100), nullable=False, server_default=''),
    Column('age', String(length=100), nullable=False, server_default=''),
    Column('gender', String(length=100), nullable=False, server_default=''),
    Column('height', String(length=100), nullable=False, server_default=''),
    Column('weight', String(length=100), nullable=False, server_default=''),
    Column('species', String(length=100), nullable=False, server_default=''),
    Column('content', String(length=100000), nullable=False, server_default=""),
    Column('rating', RatingColumn, nullable=False),
    Column('settings', CharSettingsColumn({}, length=20), nullable=False, server_default=''),
    Column('hidden', Boolean(), nullable=False, server_default='f'),
    Column('friends_only', Boolean(), nullable=False, server_default='f'),
    Column('page_views', Integer(), nullable=False, server_default='0'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='character_userid_fkey'),
)

Index('ind_character_userid', character.c.userid)


global_rate_limits = Table(
    'global_rate_limits', metadata,
    Column('id', String(length=32), primary_key=True),
    Column('available', Integer(), nullable=False, server_default="0"),
    Column('last_update', BigInteger(), nullable=False, server_default="0"),
)


google_doc_embeds = Table(
    'google_doc_embeds', metadata,
    Column('submitid', Integer(), primary_key=True, nullable=False),
    Column('embed_url', String(length=255), nullable=False),
    cascading_fkey(['submitid'], ['submission.submitid'], name='google_doc_embeds_submitid_fkey'),
)


ignoreuser = Table(
    'ignoreuser', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('otherid', Integer(), primary_key=True, nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='ignoreuser_userid_fkey'),
    cascading_fkey(['otherid'], ['login.userid'], name='ignoreuser_otherid_fkey'),
)

Index('ind_ignoreuser_userid', ignoreuser.c.userid)


journal = Table(
    'journal', metadata,
    Column('journalid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('title', String(length=200), nullable=False),
    Column('content', String(length=100000), nullable=False),
    Column('rating', RatingColumn, nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('hidden', Boolean(), nullable=False, server_default='f'),
    Column('friends_only', Boolean(), nullable=False, server_default='f'),
    Column('page_views', Integer(), nullable=False, server_default='0'),
    Column('submitter_ip_address', String(length=45), nullable=True),
    Column('submitter_user_agent_id', Integer(), nullable=True),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='journal_userid_fkey'),
    ForeignKeyConstraint(
        ['submitter_user_agent_id'],
        ['user_agents.user_agent_id'],
        name="journal_user_agent_id_fkey",
    ),
)

Index('ind_journal_userid', journal.c.userid)


journalcomment = Table(
    'journalcomment', metadata,
    Column('commentid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('targetid', Integer(), nullable=False),
    Column('parentid', Integer(), nullable=False, server_default='0'),
    Column('content', String(length=10000), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('settings', String(length=20), nullable=False, server_default=''),
    Column('hidden_by', Integer(), nullable=True),
    ForeignKeyConstraint(['targetid'], ['journal.journalid'], name='journalcomment_targetid_fkey'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='journalcomment_userid_fkey'),
    ForeignKeyConstraint(
        ['hidden_by'],
        ['login.userid'],
        name='journalcomment_hidden_by_fkey',
        ondelete='SET NULL',
    ),
)

Index('ind_journalcomment_targetid_commentid', journalcomment.c.targetid, journalcomment.c.commentid)


login = Table(
    'login', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('login_name', String(length=USERNAME_MAX_LENGTH), nullable=False, unique=True),
    Column('last_login', TIMESTAMP(timezone=True), nullable=False),
    Column('email', String(length=100), nullable=False, server_default=''),
    Column('twofa_secret', String(length=420), nullable=True),
    # Must be nullable, since existing accounts will not have this information
    Column('ip_address_at_signup', String(length=39), nullable=True),
    Column('voucher', Integer, ForeignKey('login.userid', name='login_voucher_fkey'), nullable=True),
    # Nullable for the case where no site updates exist in the database.
    Column('last_read_updateid', Integer(), nullable=True),
    ForeignKeyConstraint(['last_read_updateid'], ['siteupdate.updateid'], name='login_last_read_updateid_fkey'),
    CheckConstraint("login_name SIMILAR TO '[0-9a-z]+'", name='login_login_name_format_check'),
)

Index('ind_login_lower_email', func.lower(login.c.email.collate('C')))


twofa_recovery_codes = Table(
    'twofa_recovery_codes', metadata,
    Column('userid', Integer(), nullable=False),
    Column('recovery_code_hash', String(length=100), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='twofa_recovery_codes_userid_fkey'),
)

Index('ind_twofa_recovery_codes_userid', twofa_recovery_codes.c.userid)


logincreate = Table(
    'logincreate', metadata,
    Column('token', String(length=100), primary_key=True, nullable=False),
    Column('username', String(length=USERNAME_MAX_LENGTH), nullable=False),
    Column('login_name', String(length=USERNAME_MAX_LENGTH), nullable=False, unique=True),
    Column('hashpass', String(length=100), nullable=False),
    Column('email', String(length=100), nullable=False, unique=True),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    # Used to determine if a record is invalid for purposes of plausible deniability of email addresses
    #   AKA, create a logincreate entry if an in-use email address is provided, thus preserving the effect of
    #   a pending username triggering a username taken error.
    Column('invalid', Boolean(), server_default='f', nullable=False),
    Column('invalid_email_addr', String(length=100), nullable=True, server_default=None),
    Column('ip_address_signup_request', String(length=39), nullable=True),
    # TODO: Make `login_name` a generated column in PostgreSQL 12+
    CheckConstraint("""username SIMILAR TO '[!-~]+( [!-~]+)*' AND login_name <> '' AND login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g') COLLATE "C")""", name='logincreate_username_format_check'),
)


media = Table(
    'media', metadata,
    Column('mediaid', Integer(), primary_key=True, nullable=False),
    Column('file_type', String(length=8), nullable=False),
    Column('attributes', JSONValuesColumn(), nullable=False, server_default=text("''::hstore")),
    Column('sha256', String(length=64)),
)

Index('ind_media_sha256', media.c.sha256)


message = Table(
    'message', metadata,
    Column('noteid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('otherid', Integer(), nullable=False),
    # TODO: delete unused columns after deployment of change that removes them from queries
    Column('user_folder', Integer(), nullable=False, server_default='0'),
    Column('other_folder', Integer(), nullable=False, server_default='0'),
    Column('title', String(length=100), nullable=False),
    Column('content', String(length=100000), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('settings', String(length=20), nullable=False, server_default='u'),
    ForeignKeyConstraint(['otherid'], ['login.userid'], name='message_otherid_fkey'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='message_userid_fkey'),
)

Index('ind_message_otherid_noteid', message.c.otherid, message.c.noteid)
Index('ind_message_userid_noteid', message.c.userid, message.c.noteid)


oauth_bearer_tokens = Table(
    'oauth_bearer_tokens', metadata,
    Column('id', Integer(), primary_key=True, nullable=False),
    Column('clientid', String(length=32), nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('scopes', ARRAY(Text()), nullable=False),
    Column('access_token', String(length=64), nullable=False, unique=True),
    Column('refresh_token', String(length=64), nullable=False, unique=True),
    Column('expires_at', ArrowColumn(), nullable=False),
    ForeignKeyConstraint(['clientid'], ['oauth_consumers.clientid'], name='oauth_bearer_tokens_clientid_fkey'),
    cascading_fkey(['userid'], ['login.userid'], name='oauth_bearer_tokens_userid_fkey'),
)


oauth_consumers = Table(
    'oauth_consumers', metadata,
    Column('clientid', String(length=32), primary_key=True, nullable=False),
    Column('description', Text(), nullable=False),
    Column('ownerid', Integer(), nullable=False),
    Column('grant_type', String(length=32), nullable=False),
    Column('response_type', String(length=32), nullable=False),
    Column('scopes', ARRAY(Text()), nullable=False),
    Column('redirect_uris', ARRAY(Text()), nullable=False),
    Column('client_secret', String(length=64), nullable=False),
    ForeignKeyConstraint(['ownerid'], ['login.userid'], name='oauth_consumers_owner_fkey'),
)


permaban = Table(
    'permaban', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('reason', Text(), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='permaban_userid_fkey'),
)


permitted_senders = Table(
    'permitted_senders', metadata,
    Column('userid', Integer(), primary_key=True),
    Column('sender', Integer(), primary_key=True),
    cascading_fkey(['userid'], ['login.userid'], name='permitted_senders_userid_fkey'),
    cascading_fkey(['sender'], ['login.userid'], name='permitted_senders_sender_fkey'),
)


profile = Table(
    'profile', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('username', String(length=USERNAME_MAX_LENGTH), nullable=False, unique=True),
    Column('full_name', String(length=100), nullable=False),
    Column('catchphrase', String(length=200), nullable=False, server_default=''),
    Column('artist_type', String(length=100), nullable=False, server_default=''),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column('latest_submission_time', ArrowColumn(), nullable=False, server_default='epoch'),
    Column('profile_text', String(length=100000), nullable=False, server_default=''),
    Column('settings', String(length=20), nullable=False, server_default='ccci'),
    Column('commissions_status', ProfileStatus),
    Column('trades_status', ProfileStatus),
    Column('requests_status', ProfileStatus),
    Column('streaming_later', Boolean()),
    Column('stream_url', String(length=500), nullable=False, server_default=''),
    Column('page_views', Integer(), nullable=False, server_default='0'),
    Column('config', CharSettingsColumn({
        'b': 'show-birthday',
        '2': '12-hour-time',

        'g': 'tagging-disabled',
        'd': 'premium',

        'u': 'hide-favorites-bar',
        'v': 'hide-favorites',
        'w': 'staff-shouts-only',
        'x': 'friend-shouts-only',
        'y': 'staff-notes-only',
        'z': 'friend-notes-only',
        'h': 'hide-profile-from-guests',
        'i': 'hide-profile-stats',
        'k': 'disallow-others-tag-removal',

        's': 'watch-user-submissions',
        'c': 'watch-user-collections',
        'f': 'watch-user-characters',
        't': 'watch-user-stream-status',
        'j': 'watch-user-journals',
    }, {
        'tagging-level': {
            'a': 'max-rating-mature',
            'p': 'max-rating-explicit',
        },
        'thumbnail-bar': {
            'O': 'collections',
            'A': 'characters',
        },
    }, length=50), nullable=False, server_default=''),
    Column('show_age', Boolean()),
    Column('can_suggest_tags', Boolean(), nullable=False, server_default='t'),
    Column('premium', Boolean(), nullable=False, server_default='f'),
    Column('favorites_visibility', Permissions),
    Column('favorites_bar', Boolean()),
    Column('shouts_from', Permissions),
    Column('messages_from', Permissions),
    Column('profile_guests', Boolean()),
    Column('profile_stats', Boolean()),
    Column('max_rating', Rating),
    Column('watch_defaults', String()),
    Column('thumbnail_bar', ENUM('submissions', 'collections', 'characters', name="thumbnail_bar")),
    Column('jsonb_settings', JSONB()),
    Column('allow_collection_requests', Boolean()),
    Column('collection_notifs', Boolean()),
    Column('custom_thumbs', Boolean()),
    Column('stream_text', String(length=2000)),
    cascading_fkey(['userid'], ['login.userid'], name='profile_userid_fkey'),
    CheckConstraint("username SIMILAR TO '[!-~]+( [!-~]+)*' AND username !~ ';'", name='profile_username_format_check'),
    CheckConstraint("watch_defaults ~ '^s?c?f?t?j?$'", name='profile_watch_defaults_check'),
)


report = Table(
    'report', metadata,
    Column('target_user', Integer(), nullable=True),
    Column('target_sub', Integer(), nullable=True),
    Column('target_char', Integer(), nullable=True),
    Column('target_journal', Integer(), nullable=True),
    Column('target_comment', Integer(), nullable=True),
    Column('opened_at', ArrowColumn(), nullable=False),
    Column('urgency', Integer(), nullable=False),
    Column('closerid', Integer(), nullable=True),
    Column('settings', CharSettingsColumn({
        'r': 'under-review',
    }, length=20), nullable=False, server_default=''),
    Column('reportid', Integer(), primary_key=True, nullable=False),
    Column('closed_at', ArrowColumn(), nullable=True),
    Column('closure_reason',
           ENUM(constants.ReportClosureReason,
                name='report_closure_reason',
                metadata=metadata,
                validate_strings=True,
                values_callable=lambda enum_cls: [e.value for e in enum_cls]),
           nullable=True),
    Column('closure_explanation', Text(), nullable=True),
    ForeignKeyConstraint(['target_user'], ['login.userid'], name='report_target_user_fkey'),
    ForeignKeyConstraint(['target_sub'], ['submission.submitid'], name='report_target_sub_fkey'),
    ForeignKeyConstraint(['target_char'], ['character.charid'], name='report_target_char_fkey'),
    ForeignKeyConstraint(['target_journal'], ['journal.journalid'], name='report_target_journal_fkey'),
    ForeignKeyConstraint(['target_comment'], ['comments.commentid'], name='report_target_comment_fkey'),
    ForeignKeyConstraint(
        ['closerid'],
        ['login.userid'],
        name='report_closerid_fkey',
        ondelete='SET NULL',
    ),
    CheckConstraint(
        '((target_user IS NOT NULL)::int + (target_sub IS NOT NULL)::int '
        '  + (target_char IS NOT NULL)::int + (target_journal IS NOT NULL)::int '
        '  + (target_comment IS NOT NULL)::int) = 1',
        name='report_target_check'),
    CheckConstraint(
        '((closed_at IS NOT NULL)::int + (closure_reason IS NOT NULL)::int '
        '  + (closure_explanation IS NOT NULL)::int) IN (0, 3)',
        name='report_closure_check'),
)


reportcomment = Table(
    'reportcomment', metadata,
    Column('violation', Integer(), nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('content', String(length=2000), nullable=False, server_default=''),
    Column('commentid', Integer(), primary_key=True, nullable=False),
    Column('reportid', Integer(), nullable=False),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='reportcomment_userid_fkey'),
    ForeignKeyConstraint(['reportid'], ['report.reportid'], name='reportcomment_reportid_fkey'),
)


searchmapchar = Table(
    'searchmapchar', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False),
    Column('settings', String(), nullable=False, server_default=''),
    Column('added_by', Integer(), ForeignKey('login.userid', ondelete='SET NULL', name='searchmapchar_added_by_fkey'), nullable=True),
    cascading_fkey(['targetid'], ['character.charid'], name='searchmapchar_targetid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapchar_tagid_fkey'),
)

Index('ind_searchmapchar_tagid', searchmapchar.c.tagid)
Index('ind_searchmapchar_targetid', searchmapchar.c.targetid)


searchmapjournal = Table(
    'searchmapjournal', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False),
    Column('settings', String(), nullable=False, server_default=''),
    Column('added_by', Integer(), ForeignKey('login.userid', ondelete='SET NULL', name='searchmapjournal_added_by_fkey'), nullable=True),
    cascading_fkey(['targetid'], ['journal.journalid'], name='searchmapjournal_targetid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapjournal_tagid_fkey'),
)

Index('ind_searchmapjournal_targetid', searchmapjournal.c.targetid)
Index('ind_searchmapjournal_tagid', searchmapjournal.c.tagid)


searchmapsubmit = Table(
    'searchmapsubmit', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False),
    Column('settings', CharSettingsColumn({
        'a': 'artist-tag',
    }), nullable=False, server_default=''),
    Column('added_by', Integer(), ForeignKey('login.userid', ondelete='SET NULL', name='searchmapsubmit_added_by_fkey'), nullable=True),
    cascading_fkey(['targetid'], ['submission.submitid'], name='searchmapsubmit_targetid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='searchmapsubmit_tagid_fkey'),
)

Index('ind_searchmapsubmit_tagid', searchmapsubmit.c.tagid)
Index('ind_searchmapsubmit_targetid', searchmapsubmit.c.targetid)


artist_preferred_tags = Table(
    'artist_preferred_tags', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False),
    Column('settings', String(), nullable=False, server_default=''),
    cascading_fkey(['targetid'], ['login.userid'], name='artist_preferred_tags_targetid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='artist_preferred_tags_tagid_fkey'),
)

Index('ind_artist_preferred_tags_tagid', artist_preferred_tags.c.tagid)
Index('ind_artist_preferred_tags_targetid', artist_preferred_tags.c.targetid)


artist_optout_tags = Table(
    'artist_optout_tags', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False),
    Column('settings', String(), nullable=False, server_default=''),
    cascading_fkey(['targetid'], ['login.userid'], name='artist_optout_tags_targetid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='artist_optout_tags_tagid_fkey'),
)

Index('ind_artist_optout_tags_tagid', artist_optout_tags.c.tagid)
Index('ind_artist_optout_tags_targetid', artist_optout_tags.c.targetid)


globally_restricted_tags = Table(
    'globally_restricted_tags', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='globally_restricted_tags_userid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='globally_restricted_tags_tagid_fkey'),
)


user_restricted_tags = Table(
    'user_restricted_tags', metadata,
    Column('tagid', Integer(), nullable=False),
    Column('userid', Integer(), nullable=False),
    PrimaryKeyConstraint('userid', 'tagid'),
    cascading_fkey(['userid'], ['login.userid'], name='user_restricted_tags_userid_fkey'),
    ForeignKeyConstraint(['tagid'], ['searchtag.tagid'], name='user_restricted_tags_tagid_fkey'),
)


searchtag = Table(
    'searchtag', metadata,
    Column('tagid', Integer(), primary_key=True, nullable=False),
    Column('title', String(length=constants.TAG_MAX_LENGTH), nullable=False, unique=True),
)

Index('ind_searchtag_tagid', searchtag.c.tagid)


sessions = Table(
    'sessions', metadata,
    Column('sessionid', String(length=64), primary_key=True, nullable=False),
    Column('created_at', ArrowColumn(), nullable=False, server_default=text('now()')),
    Column('last_active', TIMESTAMP(timezone=True), nullable=True, server_default=func.now()),
    Column('userid', Integer()),
    Column('additional_data', JSONValuesColumn(), nullable=False, server_default=text("''::hstore")),
    Column('ip_address', String(length=39), nullable=True),
    Column('user_agent_id', Integer(), nullable=True),
    cascading_fkey(['userid'], ['login.userid'], name='sessions_userid_fkey'),
    ForeignKeyConstraint(['user_agent_id'], ['user_agents.user_agent_id'], name='sessions_user_agent_id_fkey'),
    CheckConstraint("userid IS NOT NULL OR additional_data != ''", name='sessions_no_guest_check'),
)

Index('ind_sessions_created_at', sessions.c.created_at)
Index('ind_sessions_last_active', sessions.c.last_active)
Index('ind_sessions_userid', sessions.c.userid)


user_agents = Table(
    'user_agents', metadata,
    Column('user_agent_id', Integer(), primary_key=True, nullable=False),
    Column('user_agent', String(length=1024), nullable=False, unique=True),
)

user_events = Table(
    'user_events', metadata,
    Column('eventid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), ForeignKey('login.userid', name='user_events_userid_fkey'), nullable=False),
    Column('event', String(length=100), nullable=False),
    Column('data', JSONB(), nullable=False),
    Column('occurred', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
)

Index('ind_user_events_userid_eventid', user_events.c.userid, user_events.c.eventid)


siteupdate = Table(
    'siteupdate', metadata,
    Column('updateid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('wesley', Boolean(), nullable=False, server_default='f'),
    Column('title', String(length=100), nullable=False),
    Column('content', Text(), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='siteupdate_userid_fkey'),
)


siteupdatecomment = Table(
    'siteupdatecomment', metadata,
    Column('commentid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('targetid', Integer(), nullable=False),
    Column('parentid', Integer(), nullable=True),
    Column('content', String(length=10000), nullable=False),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    Column('hidden_at', TIMESTAMP(timezone=True), nullable=True),
    Column('hidden_by', Integer(), nullable=True),
    ForeignKeyConstraint(['targetid'], ['siteupdate.updateid'], name='siteupdatecomment_targetid_fkey'),
    ForeignKeyConstraint(
        ['targetid', 'parentid'],
        ['siteupdatecomment.targetid', 'siteupdatecomment.commentid'],
        name='siteupdatecomment_parentid_fkey'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='siteupdatecomment_userid_fkey'),
    ForeignKeyConstraint(['hidden_by'], ['login.userid'], name='siteupdatecomment_hidden_by_fkey', ondelete='SET NULL'),
    CheckConstraint("hidden_by IS NULL OR hidden_at IS NOT NULL", name='siteupdatecomment_hidden_check'),
    UniqueConstraint('targetid', 'commentid'),
)


submission = Table(
    'submission', metadata,
    Column('submitid', Integer(), primary_key=True, nullable=False),
    Column('folderid', Integer(), nullable=True),
    Column('userid', Integer(), nullable=False),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('title', String(length=200), nullable=False),
    Column('content', String(length=300000), nullable=False),
    Column('subtype', Integer(), nullable=False),
    Column('rating', RatingColumn, nullable=False),
    Column('page_views', Integer(), nullable=False, server_default='0'),
    Column('hidden', Boolean(), nullable=False, server_default='f'),
    Column('friends_only', Boolean(), nullable=False, server_default='f'),
    Column('critique', Boolean(), nullable=False, server_default='f'),
    Column('embed_type', ENUM('google-drive', 'other', name="embed_types"), nullable=True),
    Column('favorites', Integer(), nullable=False),
    Column('submitter_ip_address', String(length=45), nullable=True),
    Column('submitter_user_agent_id', Integer(), nullable=True),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='submission_userid_fkey'),
    ForeignKeyConstraint(
        ['folderid'],
        ['folder.folderid'],
        name='submission_folderid_fkey',
        ondelete='SET NULL',
    ),
    ForeignKeyConstraint(
        ['submitter_user_agent_id'],
        ['user_agents.user_agent_id'],
        name="submission_agent_id_fkey",
    ),
    Index(
        'ind_submission_score',
        text("""(
            log(favorites + 1)
                + log(page_views + 1) / 2
                + unixtime / 180000.0
        )"""),
    ),
    Index(
        'ind_submission_score2',
        text("""(
            log(favorites)
                + unixtime / 180000.0
        )"""),
        postgresql_where=text("favorites > 0"),
    ),
)

Index('ind_submission_folderid', submission.c.folderid)
Index('ind_submission_userid_submitid', submission.c.userid, submission.c.submitid)
Index('ind_submission_userid_folderid_submitid', submission.c.userid, submission.c.folderid, submission.c.submitid, postgresql_where=submission.c.folderid.isnot(None))
Index('ind_submission_submitid_critique', submission.c.submitid, postgresql_where=submission.c.critique & ~submission.c.hidden)


submission_media_links = Table(
    'submission_media_links', metadata,
    Column('linkid', Integer(), primary_key=True, nullable=False),
    Column('mediaid', Integer(), nullable=False),
    Column('submitid', Integer(), nullable=False),
    Column('link_type', String(length=32), nullable=False),
    cascading_fkey(['submitid'], ['submission.submitid'], name='submission_media_links_submitid_fkey'),
    ForeignKeyConstraint(['mediaid'], ['media.mediaid'], name='submission_media_links_mediaid_fkey'),
)

Index('ind_submission_media_links_submitid', submission_media_links.c.submitid)
Index('ind_submission_media_links_mediaid', submission_media_links.c.mediaid, unique=False)


submission_tags = Table(
    'submission_tags', metadata,
    Column('submitid', Integer(), primary_key=True, nullable=False),
    Column('tags', ARRAY(Integer()), nullable=False),
    cascading_fkey(['submitid'], ['submission.submitid'], name='submission_tags_submitid_fkey'),
)

Index('ind_submission_tags_tags', submission_tags.c.tags, postgresql_using='gin')


suspension = Table(
    'suspension', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('reason', Text(), nullable=False),
    Column('release', Integer(), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='suspension_userid_fkey'),
)


def _tag_suggestion_feedback_table(content_table, id_column):
    table_name = f'tag_suggestion_feedback_{content_table.name}'

    return Table(
        table_name, metadata,
        Column('targetid', ForeignKey(id_column, ondelete='CASCADE', name=f'{table_name}_targetid_fkey'), primary_key=True),
        Column('tagid', ForeignKey(searchtag.c.tagid, name=f'{table_name}_tagid_fkey'), primary_key=True),
        Column('userid', ForeignKey(login.c.userid, ondelete='CASCADE', name=f'{table_name}_userid_fkey'), primary_key=True),
        Column('last_modified', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
        Column('incorrect', Boolean(), nullable=False),
        Column('unwanted', Boolean(), nullable=False),
        Column('abusive', Boolean(), nullable=False),
    )


tag_suggestion_feedback_submission = _tag_suggestion_feedback_table(submission, submission.c.submitid)
tag_suggestion_feedback_character = _tag_suggestion_feedback_table(character, character.c.charid)
tag_suggestion_feedback_journal = _tag_suggestion_feedback_table(journal, journal.c.journalid)


tag_updates = Table(
    'tag_updates', metadata,
    Column('updateid', Integer(), primary_key=True),
    Column('submitid', Integer(), nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('added', ARRAY(Text())),
    Column('removed', ARRAY(Text())),
    Column('updated_at', Integer(), nullable=False,
           server_default=text("(date_part('epoch'::text, now()) - (18000)::double precision)")),
    cascading_fkey(['submitid'], ['submission.submitid'], name='tag_updates_submitid_fkey'),
    ForeignKeyConstraint(['userid'], ['login.userid'], name='tag_updates_userid_fkey'),
)

Index('ind_tag_updates_submitid', tag_updates.c.submitid)


user_media_links = Table(
    'user_media_links', metadata,
    Column('linkid', Integer(), primary_key=True, nullable=False),
    Column('mediaid', Integer(), nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('link_type', String(length=32), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='user_media_links_userid_fkey'),
    ForeignKeyConstraint(['mediaid'], ['media.mediaid'], name='user_media_links_mediaid_fkey'),
)

Index('ind_user_media_links_submitid', user_media_links.c.userid)
Index('ind_user_media_links_userid', user_media_links.c.userid)
Index('ind_user_media_links_mediaid', user_media_links.c.mediaid, unique=False)


user_links = Table(
    'user_links', metadata,
    Column('linkid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('link_type', String(length=64), nullable=False),
    Column('link_value', String(length=2000), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='user_links_userid_fkey'),
)

Index('ind_user_links_userid', user_links.c.userid)


user_streams = Table(
    'user_streams', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('start_time', Integer(), nullable=False),
    Column('end_time', Integer(), nullable=False),
    cascading_fkey(['userid'], ['login.userid'], name='user_streams_userid_fkey'),
)

Index('ind_user_streams_end', user_streams.c.end_time)
Index('ind_user_streams_end_time', user_streams.c.end_time)


useralias = Table(
    'useralias', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('alias_name', String(length=USERNAME_MAX_LENGTH), primary_key=True, nullable=False),
    Column('settings', String(), nullable=False, server_default=''),
    cascading_fkey(['userid'], ['login.userid'], name='useralias_userid_fkey'),
    UniqueConstraint('alias_name', name='useralias_alias_name_key'),
    CheckConstraint("alias_name SIMILAR TO '[0-9a-z]+'", name='useralias_alias_name_format_check'),
)


userinfo = Table(
    'userinfo', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('birthday', Date(), nullable=True),
    Column('asserted_adult', Boolean(), nullable=False, server_default='f'),
    Column('gender', String(length=100), nullable=False, server_default=''),
    Column('country', String(length=50), nullable=False, server_default=''),
    cascading_fkey(['userid'], ['login.userid'], name='userinfo_userid_fkey'),
)


username_history = Table(
    'username_history', metadata,
    Column('historyid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), ForeignKey('login.userid', name='username_history_userid_fkey'), nullable=False),
    Column('username', String(length=USERNAME_MAX_LENGTH), nullable=False),
    Column('login_name', String(length=USERNAME_MAX_LENGTH), nullable=False),
    Column('replaced_at', TIMESTAMP(timezone=True), nullable=False),
    Column('replaced_by', Integer(), ForeignKey('login.userid', name='username_history_replaced_by_fkey'), nullable=False),
    Column('active', Boolean(), nullable=False),
    Column('deactivated_at', TIMESTAMP(timezone=True), nullable=True),
    Column('deactivated_by', Integer(), ForeignKey('login.userid', name='username_history_deactivated_by_fkey'), nullable=True),
    # true if the username changed but the login_name didn't
    Column('cosmetic', Boolean(), nullable=False),
    CheckConstraint("username SIMILAR TO '[!-~]+( [!-~]+)*' AND username !~ ';'", name='username_history_username_check'),
    # TODO: replace with generated column once on PostgreSQL 12
    CheckConstraint("""login_name <> '' AND login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g') COLLATE "C")""", name='username_history_login_name_check'),
    CheckConstraint("(active OR cosmetic) = (deactivated_at IS NULL) AND (active OR cosmetic) = (deactivated_by IS NULL)", name='username_history_active_check'),
    CheckConstraint("NOT (cosmetic AND active)", name='username_history_cosmetic_inactive_check'),
)

# enforces one active redirect per user
Index('ind_username_history_userid', username_history.c.userid, postgresql_where=username_history.c.active, unique=True)

# enforces that active redirects have unique usernames within this table, although they also need to be unique in all of login, logincreate, useralias, and username_history together
Index('ind_username_history_login_name', username_history.c.login_name, postgresql_where=username_history.c.active, unique=True)

# lookup for a user's most recent change
Index('ind_username_history_userid_historyid', username_history.c.userid, username_history.c.historyid, postgresql_where=~username_history.c.cosmetic, unique=True)


views = Table(
    'views', metadata,
    Column('viewer', String(length=127), primary_key=True, nullable=False),
    Column('targetid', Integer(), primary_key=True, nullable=False, autoincrement=False),
    Column('type', Integer(), primary_key=True, nullable=False, autoincrement=False),
    Column('viewed_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
)

Index('ind_views_viewed_at', views.c.viewed_at)


watchuser = Table(
    'watchuser', metadata,
    Column('userid', Integer(), primary_key=True, nullable=False),
    Column('otherid', Integer(), primary_key=True, nullable=False),
    Column('settings', String(length=20), nullable=False),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    ForeignKeyConstraint(['otherid'], ['login.userid'], name='watchuser_otherid_fkey'),
    cascading_fkey(['userid'], ['login.userid'], name='watchuser_userid_fkey'),
)

Index('ind_watchuser_userid', watchuser.c.userid)
Index('ind_watchuser_settings', watchuser.c.settings)
Index('ind_watchuser_userid_settings', watchuser.c.userid, watchuser.c.settings)
Index('ind_watchuser_otherid', watchuser.c.otherid)
Index('ind_watchuser_otherid_settings', watchuser.c.otherid, watchuser.c.settings)


welcome = Table(
    'welcome', metadata,
    Column('welcomeid', Integer(), primary_key=True, nullable=False),
    Column('userid', Integer(), nullable=False),
    Column('otherid', Integer(), nullable=False),
    Column('referid', Integer(), nullable=False, server_default='0'),
    Column('targetid', Integer(), nullable=False, server_default='0'),
    Column('unixtime', WeasylTimestampColumn(), nullable=False),
    Column('type', Integer(), nullable=False),
    Column('deleted', ArrowColumn()),
    cascading_fkey(['userid'], ['login.userid'], name='welcome_userid_fkey'),
)

Index('ind_welcome_otherid', welcome.c.otherid)
Index('ind_welcome_referid', welcome.c.referid)
Index('ind_welcome_targetid', welcome.c.targetid)
Index('ind_welcome_type', welcome.c.type)
Index('ind_welcome_unixtime', welcome.c.unixtime)
Index('ind_welcome_userid_type', welcome.c.userid, welcome.c.type)

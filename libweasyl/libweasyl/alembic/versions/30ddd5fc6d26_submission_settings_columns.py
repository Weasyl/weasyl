"""Replace character settings column in submissions with individual columns.

Note that there are some characters in a settings column that didn't seem code-relevant.
downgrading will not restore these.

Revision ID: 30ddd5fc6d26
Revises: 40c00abab5f9
Create Date: 2017-01-16 20:33:02.166099

"""

# revision identifiers, used by Alembic.
revision = '30ddd5fc6d26'
down_revision = '40c00abab5f9'

from alembic import op
import sqlalchemy as sa

import libweasyl

def upgrade():
    op.add_column(
        'submission',
        sa.Column('hidden', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('friends_only', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('critique', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('tag_locked', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('comment_locked', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('admin_locked', sa.Boolean(), nullable=False, server_default=False),
    )
    op.add_column(
        'submission',
        sa.Column('embed_type', sa.Enum('google-drive', 'other'), nullable=True),

    )
    op.execute(
        """
        UPDATE submission SET
            hidden = CASE WHEN settings ~ 'h' THEN TRUE ELSE FALSE END,
            friends_only = CASE WHEN settings ~ 'f' THEN TRUE ELSE FALSE END,
            critique = CASE WHEN settings ~ 'q' THEN TRUE ELSE FALSE END,
            tag_locked = CASE WHEN settings ~ 't' THEN TRUE ELSE FALSE END,
            comment_locked = CASE WHEN settings ~ 'c' THEN TRUE ELSE FALSE END,
            admin_locked = CASE WHEN settings ~ 'a' THEN TRUE ELSE FALSE END
            embed_type = CASE
                WHEN settings ~ 'D' THEN 'google-drive'
                WHEN settings ~ 'v' THEN 'other'
            END
        """)
    op.drop_column('submission', 'settings')

def downgrade():
    op.add_column(
        'submission',
        sa.Column('settings', libweasyl.models.helpers.CharSettingsColumn({
            'h': 'hidden',
            'f': 'friends-only',
            'q': 'critique',
            'p': 'pool',
            'o': 'collaboration',
            't': 'tag-locked',
            'c': 'comment-locked',
            'a': 'admin-locked',
            'e': 'encored',
            'u': 'thumbnail-required',
        }, {
            'embed-type': {
                'D': 'google-drive',
                'v': 'other',
            },
        }), nullable=False, server_default=''),
    )
    op.execute(
        """
        UPDATE submission SET settings =
            CASE WHEN hidden THEN 'h' ELSE '' END
            || CASE WHEN friends_only THEN 'f' ELSE '' END
            || CASE WHEN critique THEN 'q' ELSE '' END
            || CASE WHEN tag_locked THEN 't' ELSE '' END
            || CASE WHEN comment_locked THEN 'c' ELSE '' END
            || CASE WHEN admin_locked THEN 'a' ELSE '' END
            || CASE
                 WHEN embed_type = 'google-drive' THEN 'D'
                 WHEN embed_type = 'other' THEN 'v'
                 ELSE ''
               END
        """
    )
    op.drop_column('submission', 'hidden')
    op.drop_column('submission', 'friends_only')
    op.drop_column('submission', 'critique')
    op.drop_column('submission', 'tag_locked')
    op.drop_column('submission', 'comment_locked')
    op.drop_column('submission', 'admin_locked')
    op.drop_column('submission', 'embed_type')

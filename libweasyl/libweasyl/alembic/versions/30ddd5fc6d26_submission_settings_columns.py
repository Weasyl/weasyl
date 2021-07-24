"""Replace character settings column in submissions with individual columns.

Note that there are some characters in a settings column that didn't seem code-relevant.
downgrading will not restore these.

Revision ID: 30ddd5fc6d26
Revises: af3b8d60b7ba
Create Date: 2017-01-16 20:33:02.166099

"""

# revision identifiers, used by Alembic.
revision = '30ddd5fc6d26'
down_revision = 'af3b8d60b7ba'

from alembic import op
import sqlalchemy as sa

import libweasyl.models.helpers

embed_types = sa.Enum('google-drive', 'other', name="embed_types")

def upgrade():
    embed_types.create(op.get_bind())
    op.add_column(
        'submission',
        sa.Column('hidden', sa.Boolean(), nullable=False, server_default='f'),
    )
    op.add_column(
        'submission',
        sa.Column('friends_only', sa.Boolean(), nullable=False, server_default='f'),
    )
    op.add_column(
        'submission',
        sa.Column('critique', sa.Boolean(), nullable=False, server_default='f'),
    )
    op.add_column(
        'submission',
        sa.Column('embed_type', embed_types, nullable='f'),

    )
    op.execute(
        """
        UPDATE submission SET
            hidden = settings ~ 'h',
            friends_only = settings ~ 'f',
            critique = settings ~ 'q',
            embed_type = (CASE
                WHEN settings ~ 'D' THEN 'google-drive'::embed_types
                WHEN settings ~ 'v' THEN 'other'::embed_types
            END)
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
    op.drop_column('submission', 'embed_type')
    embed_types.drop(op.get_bind())


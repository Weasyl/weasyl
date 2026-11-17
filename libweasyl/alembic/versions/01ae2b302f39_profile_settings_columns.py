"""Profile settings columns

Revision ID: 01ae2b302f39
Revises: bb2c42b6df18
Create Date: 2025-07-21 17:30:59.295311

"""

# revision identifiers, used by Alembic.
revision = '01ae2b302f39'
down_revision = 'bb2c42b6df18'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


Permissions = postgresql.ENUM('nobody', 'friends', 'everyone', name='permissions')
ProfileStatus = postgresql.ENUM('exclude', 'closed', 'filled', 'sometimes', 'open', name='profile_status')


def upgrade():
    op.execute("CREATE TYPE permissions AS ENUM ('nobody', 'friends', 'everyone')")
    op.execute("CREATE TYPE rating AS ENUM ('general', 'mature', 'explicit')")
    op.execute("CREATE TYPE thumbnail_bar AS ENUM ('submissions', 'collections', 'characters')")
    op.execute("CREATE TYPE profile_status AS ENUM ('exclude', 'closed', 'filled', 'sometimes', 'open')")

    op.add_column('profile', sa.Column('show_age', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('can_suggest_tags', sa.Boolean(), server_default='t', nullable=False))
    op.add_column('profile', sa.Column('premium', sa.Boolean(), server_default='f', nullable=False))
    op.add_column('profile', sa.Column('favorites_visibility', Permissions, nullable=True))
    op.add_column('profile', sa.Column('favorites_bar', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('shouts_from', Permissions, nullable=True))
    op.add_column('profile', sa.Column('messages_from', Permissions, nullable=True))
    op.add_column('profile', sa.Column('profile_guests', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('profile_stats', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('max_rating', postgresql.ENUM('general', 'mature', 'explicit', name='rating'), nullable=True))
    op.add_column('profile', sa.Column('watch_defaults', sa.String(), nullable=True))
    op.add_column('profile', sa.Column('thumbnail_bar', postgresql.ENUM('submissions', 'collections', 'characters', name='thumbnail_bar'), nullable=True))
    op.add_column('profile', sa.Column('allow_collection_requests', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('collection_notifs', sa.Boolean(), nullable=True))
    op.add_column('profile', sa.Column('custom_thumbs', sa.Boolean(), nullable=True))
    op.create_check_constraint(
        'profile_watch_defaults_check',
        'profile',
        "watch_defaults ~ '^s?c?f?t?j?$'",
    )

    op.add_column('profile', sa.Column('commissions_status', ProfileStatus, nullable=True))
    op.add_column('profile', sa.Column('trades_status', ProfileStatus, nullable=True))
    op.add_column('profile', sa.Column('requests_status', ProfileStatus, nullable=True))

    op.add_column('profile', sa.Column('streaming_later', sa.Boolean(), nullable=True))

    # `premium` defaults to false, `can_suggest_tags` defaults to true; we’re counting on these settings not being updated between migration and app deployment. (The former can’t be changed within the app, and the latter can only be changed by admins.)
    op.execute("UPDATE profile SET premium = settings ~ 'd', can_suggest_tags = settings !~ 'g' WHERE settings ~ '[gd]'")


def downgrade():
    op.drop_constraint('profile_watch_defaults_check', 'profile')
    op.drop_column('profile', 'custom_thumbs')
    op.drop_column('profile', 'collection_notifs')
    op.drop_column('profile', 'allow_collection_requests')
    op.drop_column('profile', 'thumbnail_bar')
    op.drop_column('profile', 'watch_defaults')
    op.drop_column('profile', 'max_rating')
    op.drop_column('profile', 'profile_stats')
    op.drop_column('profile', 'profile_guests')
    op.drop_column('profile', 'messages_from')
    op.drop_column('profile', 'shouts_from')
    op.drop_column('profile', 'favorites_bar')
    op.drop_column('profile', 'favorites_visibility')
    op.drop_column('profile', 'premium')
    op.drop_column('profile', 'can_suggest_tags')
    op.drop_column('profile', 'show_age')

    op.drop_column('profile', 'commissions_status')
    op.drop_column('profile', 'trades_status')
    op.drop_column('profile', 'requests_status')

    op.drop_column('profile', 'streaming_later')

    op.execute("DROP TYPE permissions")
    op.execute("DROP TYPE rating")
    op.execute("DROP TYPE thumbnail_bar")
    op.execute("DROP TYPE profile_status")

"""Fix restricted tags constraints/indexes

Revision ID: d5eaed9d240e
Revises: a49795aa2584
Create Date: 2026-01-01 05:56:38.817187

"""

# revision identifiers, used by Alembic.
revision = 'd5eaed9d240e'
down_revision = 'a49795aa2584'

from alembic import op


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("ALTER TABLE globally_restricted_tags DROP CONSTRAINT globally_restricted_tags_pkey, ADD PRIMARY KEY (tagid)")
        op.execute("ALTER TABLE user_restricted_tags DROP CONSTRAINT user_restricted_tags_pkey, ADD PRIMARY KEY (userid, tagid)")

        op.drop_index(op.f('ind_globally_restricted_tags_tagid'), table_name='globally_restricted_tags', if_exists=True)
        op.drop_index(op.f('ind_globally_restricted_tags_userid'), table_name='globally_restricted_tags', if_exists=True)
        op.drop_index(op.f('ind_user_restricted_tags_tagid'), table_name='user_restricted_tags', if_exists=True)
        op.drop_index(op.f('ind_user_restricted_tags_userid'), table_name='user_restricted_tags', if_exists=True)


def downgrade():
    with op.get_context().autocommit_block():
        op.create_index(op.f('ind_user_restricted_tags_userid'), 'user_restricted_tags', ['userid'], unique=False, if_not_exists=True)
        op.create_index(op.f('ind_user_restricted_tags_tagid'), 'user_restricted_tags', ['tagid'], unique=False, if_not_exists=True)
        op.create_index(op.f('ind_globally_restricted_tags_userid'), 'globally_restricted_tags', ['userid'], unique=False, if_not_exists=True)
        op.create_index(op.f('ind_globally_restricted_tags_tagid'), 'globally_restricted_tags', ['tagid'], unique=False, if_not_exists=True)

        op.execute("ALTER TABLE globally_restricted_tags DROP CONSTRAINT globally_restricted_tags_pkey, ADD PRIMARY KEY (tagid, userid)")
        op.execute("ALTER TABLE user_restricted_tags DROP CONSTRAINT user_restricted_tags_pkey, ADD PRIMARY KEY (tagid, userid)")

"""More username constraints

Revision ID: 31eac938cb1d
Revises: 63baa2713e72
Create Date: 2024-11-15 20:23:34.880165

"""

# revision identifiers, used by Alembic.
revision = '31eac938cb1d'
down_revision = '63baa2713e72'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # redundant index (there’s already a `UNIQUE` constraint on `login_name`)
    op.drop_index('ind_login_login_name', table_name='login')

    # new constraints
    op.create_check_constraint(
        'login_login_name_format_check',
        'login',
        "login_name SIMILAR TO '[0-9a-z]+'",
    )
    op.execute("UPDATE logincreate SET username = regexp_replace(trim(username), ' {2,}', ' ', 'g') WHERE username ~ '^ | {2}| $'")
    op.create_check_constraint(
        'logincreate_username_format_check',
        'logincreate',
        """username SIMILAR TO '[!-~]+( [!-~]+)*' AND login_name <> '' AND login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g') COLLATE "C")""",
    )
    op.execute("UPDATE profile SET username = regexp_replace(trim(username), ' {2,}', ' ', 'g') WHERE username ~ '^ | {2}| $'")
    op.create_check_constraint(
        'profile_username_format_check',
        'profile',
        "username SIMILAR TO '[!-~]+( [!-~]+)*' AND username !~ ';'",
    )
    op.create_check_constraint(
        'useralias_alias_name_format_check',
        'useralias',
        "alias_name SIMILAR TO '[0-9a-z]+'",
    )

    # username_history_username_check
    op.execute("UPDATE username_history SET username = regexp_replace(trim(username), ' {2,}', ' ', 'g') WHERE username ~ '^ | {2}| $'")
    op.drop_constraint(
        'username_history_username_check',
        'username_history',
        type_='check',
    )
    op.create_check_constraint(
        'username_history_username_check',
        'username_history',
        "username SIMILAR TO '[!-~]+( [!-~]+)*' AND username !~ ';'",
    )

    # username_history_login_name_check
    op.drop_constraint(
        'username_history_login_name_check',
        'username_history',
        type_='check',
    )
    op.create_check_constraint(
        'username_history_login_name_check',
        'username_history',
        """login_name <> '' AND login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g') COLLATE "C")""",
    )

    op.alter_column('login', 'login_name',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=25),
               existing_nullable=False)
    op.alter_column('logincreate', 'username',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=25),
               existing_nullable=False)
    op.alter_column('logincreate', 'login_name',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=25),
               existing_nullable=False)
    op.alter_column('profile', 'username',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=25),
               existing_nullable=False)
    op.alter_column('useralias', 'alias_name',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=25),
               existing_nullable=False)
    op.create_unique_constraint('useralias_alias_name_key', 'useralias', ['alias_name'])


def downgrade():
    op.drop_constraint(
        'login_login_name_format_check',
        'login',
        type_='check',
    )
    op.drop_constraint(
        'logincreate_username_format_check',
        'logincreate',
        type_='check',
    )
    op.drop_constraint(
        'profile_username_format_check',
        'profile',
        type_='check',
    )
    op.drop_constraint(
        'useralias_alias_name_format_check',
        'useralias',
        type_='check',
    )

    # username_history_username_check
    op.drop_constraint(
        'username_history_username_check',
        'username_history',
        type_='check',
    )
    op.create_check_constraint(
        'username_history_username_check',
        'username_history',
        "username !~ '[^ -~]' AND username !~ ';'",
    )

    # username_history_login_name_check
    op.drop_constraint(
        'username_history_login_name_check',
        'username_history',
        type_='check',
    )
    op.create_check_constraint(
        'username_history_login_name_check',
        'username_history',
        "login_name = lower(regexp_replace(username, '[^0-9A-Za-z]', '', 'g'))",
    )

    op.drop_constraint('useralias_alias_name_key', 'useralias', type_='unique')
    op.alter_column('useralias', 'alias_name',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)
    op.alter_column('profile', 'username',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)
    op.alter_column('logincreate', 'login_name',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)
    op.alter_column('logincreate', 'username',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)
    op.alter_column('login', 'login_name',
               existing_type=sa.String(length=25),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)

    op.create_index('ind_login_login_name', 'login', ['login_name'], unique=False)

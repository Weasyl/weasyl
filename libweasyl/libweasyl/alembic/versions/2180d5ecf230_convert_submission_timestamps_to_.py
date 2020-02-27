"""convert submission timestamps to DateTime

Revision ID: 2180d5ecf230
Revises: 62439d6052ed
Create Date: 2020-02-26 19:25:57.702000

"""

# revision identifiers, used by Alembic.
revision = '2180d5ecf230'
down_revision = '62439d6052ed'

from alembic import op   # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]


def upgrade():
    op.drop_index('ind_submission_userid_unixtime', table_name='submission')
    op.drop_index('ind_submission_score', table_name='submission')
    op.alter_column('submission', 'unixtime',
               existing_type=sa.INTEGER(),
               server_default=sa.func.now(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="timestamp with time zone 'epoch' + (unixtime-18000) * interval '1 second';",
               new_column_name='timestamp')
    op.create_index('ind_submission_userid_timestamp', 'submission', ['userid', sa.text(u'timestamp DESC')], unique=False)
    op.create_index(
        'ind_submission_score',
        'submission',
        [
            sa.text("""(log(favorites + 1)
                + log(page_views + 1) / 2
                + EXTRACT(EPOCH FROM timestamp at time zone 'UTC')  / 180000.0
        )"""),
        ],
        unique=False,
        postgresql_where=sa.text("favorites IS NOT NULL"),
    )


def downgrade():
    pass

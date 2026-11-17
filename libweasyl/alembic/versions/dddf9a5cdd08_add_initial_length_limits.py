"""Add initial length limits

Revision ID: dddf9a5cdd08
Revises: 8cde5e07b63f
Create Date: 2018-03-10 12:20:17.091148

"""

# revision identifiers, used by Alembic.
revision = 'dddf9a5cdd08'
down_revision = '8cde5e07b63f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("UPDATE journalcomment SET content = substring(content for 10000) WHERE length(content) > 10000")
    op.execute("UPDATE searchtag SET title = substring(title for 162) WHERE length(title) > 162")

    op.alter_column('ads', 'owner',
               existing_type=sa.TEXT(),
               type_=sa.String(length=254),
               existing_nullable=False)
    op.alter_column('character', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100000),
               existing_nullable=False,
               existing_server_default=sa.text(u"''::text"))
    op.alter_column('charcomment', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=10000),
               existing_nullable=False)
    op.alter_column('commishdesc', 'content',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=20000),
               existing_nullable=False)
    op.alter_column('journal', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100000),
               existing_nullable=False)
    op.alter_column('journalcomment', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=10000),
               existing_nullable=False)
    op.alter_column('message', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100000),
               existing_nullable=False)
    op.alter_column('premiumpurchase', 'email',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=254),
               existing_nullable=False)
    op.alter_column('profile', 'profile_text',
               existing_type=sa.TEXT(),
               type_=sa.String(length=100000),
               existing_nullable=False,
               existing_server_default=sa.text(u"''::text"))
    op.alter_column('profile', 'stream_text',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=2000),
               existing_nullable=True)
    op.alter_column('searchtag', 'title',
               existing_type=sa.TEXT(),
               type_=sa.String(length=162),
               existing_nullable=False)
    op.alter_column('submission', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(length=300000),
               existing_nullable=False)
    op.alter_column('user_links', 'link_value',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=2000),
               existing_nullable=False)


def downgrade():
    op.alter_column('user_links', 'link_value',
               existing_type=sa.String(length=2000),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('submission', 'content',
               existing_type=sa.String(length=300000),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('searchtag', 'title',
               existing_type=sa.String(length=162),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('profile', 'stream_text',
               existing_type=sa.String(length=2000),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    op.alter_column('profile', 'profile_text',
               existing_type=sa.String(length=100000),
               type_=sa.TEXT(),
               existing_nullable=False,
               existing_server_default=sa.text(u"''::text"))
    op.alter_column('premiumpurchase', 'email',
               existing_type=sa.String(length=254),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('message', 'content',
               existing_type=sa.String(length=100000),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('journalcomment', 'content',
               existing_type=sa.String(length=10000),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('journal', 'content',
               existing_type=sa.String(length=100000),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('commishdesc', 'content',
               existing_type=sa.String(length=20000),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('charcomment', 'content',
               existing_type=sa.String(length=10000),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.alter_column('character', 'content',
               existing_type=sa.String(length=100000),
               type_=sa.TEXT(),
               existing_nullable=False,
               existing_server_default=sa.text(u"''::text"))
    op.alter_column('ads', 'owner',
               existing_type=sa.String(length=254),
               type_=sa.TEXT(),
               existing_nullable=False)

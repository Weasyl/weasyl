import sqlalchemy as sa
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy import func

from libweasyl import staff
from libweasyl.cache import region
from libweasyl.legacy import UNIXTIME_NOW_SQL
from libweasyl.models import tables as t
from weasyl import define as d
from weasyl import media


_SELECT_BASE = (
    sa.select(
        t.siteupdate.c.updateid,
        t.profile.c.userid,
        t.siteupdate.c.title,
        t.siteupdate.c.content,
        sa.type_coerce(t.siteupdate.c.unixtime, sa.Integer()).label('unixtime'),
        t.profile.c.username,
    )
    .select_from(
        t.siteupdate.outerjoin(t.profile, t.profile.c.userid == sa.case(
            (t.siteupdate.c.wesley, sa.bindparam('wesley', callable_=lambda: staff.WESLEY)),
            else_=t.siteupdate.c.userid,
        ))
    )
)

_SELECT_VIEW = (
    _SELECT_BASE
    .add_columns(t.siteupdate.c.wesley)
    .where(t.siteupdate.c.updateid == sa.bindparam("updateid"))
)

_SELECT_LAST = (
    _SELECT_BASE
    .add_columns(
        sa.select(func.count())
        .select_from(t.siteupdatecomment)
        .where(t.siteupdatecomment.c.targetid == t.siteupdate.c.updateid)
        .where(t.siteupdatecomment.c.hidden_at.is_(None))
        .label("comment_count"),
    )
    .order_by(t.siteupdate.c.updateid.desc())
    .limit(1)
).compile()

_SELECT_LIST = (
    _SELECT_BASE
    .order_by(t.siteupdate.c.updateid.desc())
).compile()

_CREATE = (
    t.siteupdate.insert()
    .values({
        "userid": sa.bindparam("userid"),
        "title": sa.bindparam("title"),
        "content": sa.bindparam("content"),
        "wesley": sa.bindparam("wesley"),
        "unixtime": UNIXTIME_NOW_SQL,
    })
    .returning(t.siteupdate.c.updateid)
).compile()

_EDIT = (
    t.siteupdate.update()
    .where(t.siteupdate.c.updateid == sa.bindparam("updateid"))
    .values({
        "title": sa.bindparam("title"),
        "content": sa.bindparam("content"),
        "wesley": sa.bindparam("wesley"),
    })
).compile()


@region.cache_on_arguments(should_cache_fn=bool)
def select_view(updateid):
    update = d.engine.execute(_SELECT_VIEW, {"updateid": updateid}).one_or_none()

    if update is None:
        raise HTTPNotFound()

    return {
        **update,
        "user_media": media.get_user_media(update.userid),
    }


@region.cache_on_arguments()
def select_last():
    last = d.engine.execute(_SELECT_LAST).one_or_none()

    if last is None:
        return None

    return {
        **last,
        "user_media": media.get_user_media(last.userid),
    }


def select_list():
    updates = [row._asdict() for row in d.engine.execute(_SELECT_LIST)]
    media.populate_with_user_media(updates)
    return updates


def create(*, userid, title, content, wesley):
    updateid = d.engine.execute(_CREATE, {
        "userid": userid,
        "title": title,
        "content": content,
        "wesley": wesley,
    }).scalar_one()

    select_last.invalidate()

    return updateid


def edit(*, updateid, title, content, wesley):
    result = d.engine.execute(_EDIT, {
        "updateid": updateid,
        "title": title,
        "content": content,
        "wesley": wesley,
    })

    if result.rowcount != 1:
        raise HTTPNotFound()

    select_view.invalidate(updateid)
    select_last.invalidate()

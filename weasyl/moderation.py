import collections
import datetime

import arrow
import sqlalchemy as sa

from libweasyl.legacy import get_offset_unixtime
from libweasyl.models.content import Submission
from libweasyl import ratings, staff, text

from weasyl import avatar
from weasyl import banner
from weasyl import character
from weasyl import define as d
from weasyl import index
from weasyl import media
from weasyl import profile
from weasyl import shout
from weasyl import submission
from weasyl import thumbnail
from weasyl.error import WeasylError
from weasyl.forms import parse_sysname
from weasyl.macro import MACRO_SUPPORT_ADDRESS


def get_ban_reason(userid):
    return d.engine.scalar("SELECT reason FROM permaban WHERE userid = %(user)s",
                           user=userid)


def get_suspension(userid):
    return d.engine.execute("SELECT reason, release FROM suspension WHERE userid = %(user)s",
                            user=userid).first()


def get_ban_message(userid):
    reason = get_ban_reason(userid)
    return (
        "Your account has been permanently banned and you are no longer allowed "
        "to sign in.\n\n%s\n\nIf you believe this ban is in error, please "
        "contact %s for assistance."
    ) % (reason, MACRO_SUPPORT_ADDRESS)


def get_suspension_message(userid):
    suspension = get_suspension(userid)
    release = d.get_arrow(suspension.release)
    return (
        "Your account has been temporarily suspended and you are not allowed to "
        "be logged in at this time.\n\n%s\n\nThis suspension will be lifted on "
        "%s.\n\nIf you believe this suspension is in error, please contact "
        "%s for assistance."
    ) % (suspension.reason, release.date(), MACRO_SUPPORT_ADDRESS)


def finduser(targetid, username: str, email: str, dateafter, datebefore, excludesuspended, excludebanned, excludeactive, ipaddr,
             row_offset):
    targetid = d.get_int(targetid)

    # If we don't have any of these variables, nothing will be displayed. So fast-return an empty list.
    if not targetid and not username and not email and not dateafter \
            and not datebefore and not excludesuspended and not excludebanned \
            and not excludeactive and not ipaddr:
        return []

    lo = d.meta.tables['login']
    sh = d.meta.tables['comments']
    pr = d.meta.tables['profile']
    sess = d.meta.tables['sessions']
    permaban = d.meta.tables['permaban']
    suspension = d.meta.tables['suspension']

    is_banned = sa.exists(
        sa.select([])
        .select_from(permaban)
        .where(permaban.c.userid == lo.c.userid)
    ).label('is_banned')

    is_suspended = sa.exists(
        sa.select([])
        .select_from(suspension)
        .where(suspension.c.userid == lo.c.userid)
    ).label('is_suspended')

    q = sa.select([
        lo.c.userid,
        lo.c.login_name,
        lo.c.email,
        (sa.select([sa.func.count()])
         .select_from(sh)
         .where(sh.c.target_user == lo.c.userid)
         .where(sh.c.settings.op('~')('s'))).label('staff_notes'),
        is_banned,
        is_suspended,
        lo.c.ip_address_at_signup,
        (sa.select([sess.c.ip_address])
            .select_from(sess)
            .where(lo.c.userid == sess.c.userid)
            .limit(1)
            .order_by(sess.c.created_at.desc())
            .correlate(sess)
         ).label('ip_address_session'),
    ]).select_from(
        lo.join(pr, lo.c.userid == pr.c.userid)
          .join(sess, sess.c.userid == pr.c.userid, isouter=True)
    )

    # Is there a better way to only select unique accounts, when _also_ joining sessions? This _does_ work, though.
    q = q.distinct(lo.c.login_name)

    if targetid:
        q = q.where(lo.c.userid == targetid)
    elif username:
        q = q.where(lo.c.login_name.ilike(f"%{username}%"))
    elif email:
        q = q.where(lo.c.email.ilike(f"%{email}%"))

    # Filter for banned and/or suspended accounts
    if excludeactive == "on":
        q = q.where(is_banned | is_suspended)
    if excludebanned == "on":
        q = q.where(~is_banned)
    if excludesuspended == "on":
        q = q.where(~is_suspended)

    # Filter for IP address
    if ipaddr:
        q = q.where(sa.or_(
            lo.c.ip_address_at_signup.op('ilike')('%s%%' % ipaddr),
            sess.c.ip_address.op('ilike')('%s%%' % ipaddr)
        ))

    # Filter for date-time
    if dateafter and datebefore:
        q = q.where(sa.between(pr.c.created_at, arrow.get(dateafter).datetime, arrow.get(datebefore).datetime))
    elif dateafter:
        q = q.where(pr.c.created_at >= arrow.get(dateafter).datetime)
    elif datebefore:
        q = q.where(pr.c.created_at <= arrow.get(datebefore).datetime)

    # Apply any row offset
    if row_offset:
        q = q.offset(row_offset)

    q = q.limit(250).order_by(lo.c.login_name.asc())
    db = d.connect()
    return db.execute(q)


_mode_to_action_map = {
    'b': 'ban',
    's': 'suspend',
    'x': 'release',
}


def setusermode(userid, form):
    form.userid = profile.resolve(None, form.userid, form.username)
    if not form.userid:
        raise WeasylError('noUser')

    form.reason = form.reason.strip()

    if form.mode == "s":
        today = datetime.datetime.utcnow().date()

        if form.datetype == "r":
            # Relative date
            magnitude = int(form.duration)
            if form.durationunit == "y":
                duration = datetime.timedelta(days=magnitude * 365)
            elif form.durationunit == "m":
                duration = datetime.timedelta(days=magnitude * 30)
            elif form.durationunit == "w":
                duration = datetime.timedelta(weeks=magnitude)
            else:  # Catchall, days
                duration = datetime.timedelta(days=magnitude)

            release_date = today + duration
        else:
            # Absolute date
            try:
                release_date = datetime.date.fromisoformat(form["release-date"])
            except ValueError as e:
                raise WeasylError("releaseInvalid") from e

        if release_date <= today:
            raise WeasylError("releaseInvalid")
    else:
        release_date = None

    if userid not in staff.MODS:
        raise WeasylError("Unexpected")
    elif form.userid in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    if form.mode == "b":
        # Ban user
        with d.engine.begin() as db:
            db.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
            db.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)
            db.execute("INSERT INTO permaban VALUES (%(target)s, %(reason)s)", target=form.userid, reason=form.reason)
    elif form.mode == "s":
        # Suspend user
        if release_date is None:
            raise WeasylError("releaseInvalid")

        release_unixtime = get_offset_unixtime(arrow.get(release_date).datetime)

        with d.engine.begin() as db:
            db.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
            db.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)
            db.execute("INSERT INTO suspension VALUES (%(target)s, %(reason)s, %(release)s)", target=form.userid, reason=form.reason, release=release_unixtime)
    elif form.mode == "x":
        # Unban/Unsuspend
        with d.engine.begin() as db:
            db.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
            db.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)

    action = _mode_to_action_map.get(form.mode)
    if action is not None:
        isoformat_release = None
        message = form.reason
        if release_date is not None:
            message = '#### Release date: %s\n\n%s' % (release_date.isoformat(), message)
        d.append_to_log(
            'staff.actions',
            userid=userid, action=action, target=form.userid, reason=form.reason,
            release=isoformat_release)
        d._get_all_config.invalidate(form.userid)
        note_about(userid, form.userid, 'User mode changed: action was %r' % (action,), message)


def submissionsbyuser(targetid):
    query = d.engine.execute("""
        SELECT submitid, title, rating, unixtime, hidden, friends_only, critique
        FROM submission
        WHERE userid = %(user)s
    """, user=targetid)

    ret = [{
        "contype": 10,
        "userid": targetid,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "hidden": i[4],
        "friends_only": i[5],
        "critique": i[6],
    } for i in query]
    media.populate_with_submission_media(ret)
    return ret


def charactersbyuser(targetid):
    query = d.engine.execute("""
        SELECT charid, unixtime, char_name, rating, settings, hidden, friends_only
        FROM character
        WHERE userid = %(user)s
    """, user=targetid)

    return [{
        "contype": 20,
        "userid": targetid,
        "charid": item.charid,
        "unixtime": item.unixtime,
        "title": item.char_name,
        "rating": item.rating,
        "hidden": item.hidden,
        "friends_only": item.friends_only,
        "critique": False,
        "sub_media": character.fake_media_items(item.charid, targetid, "unused", item.settings),
    } for item in query]


def journalsbyuser(targetid):
    query = d.engine.execute("""
        SELECT journalid, title, hidden, friends_only, unixtime, rating
        FROM journal
        WHERE userid = %(user)s
    """, user=targetid)

    return [{
        **item,
        "contype": 30,
        "critique": False,
    } for item in query]


def gallery_blacklisted_tags(userid, otherid):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    query = d.engine.execute("""
        SELECT title FROM
            (
                SELECT tagid
                FROM submission
                    INNER JOIN searchmapsubmit ON submitid = targetid
                    INNER JOIN blocktag USING (tagid)
                WHERE submission.userid = %(other)s
                    AND blocktag.userid = %(user)s
                    AND submission.rating >= blocktag.rating
                UNION SELECT tagid
                FROM character
                    INNER JOIN searchmapchar ON charid = targetid
                    INNER JOIN blocktag USING (tagid)
                WHERE character.userid = %(other)s
                    AND blocktag.userid = %(user)s
                    AND character.rating >= blocktag.rating
            ) AS t
            INNER JOIN searchtag USING (tagid)
            ORDER BY title
    """, user=userid, other=otherid)

    return [row.title for row in query]


def manageuser(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    query = d.engine.execute(
        "SELECT userid, username, config, profile_text, catchphrase FROM profile"
        " WHERE userid = (SELECT userid FROM login WHERE login_name = %(name)s)",
        name=parse_sysname(form.name),
    ).first()

    if not query:
        raise WeasylError("noUser")

    return {
        "userid": query[0],
        "username": query[1],
        "config": query[2],
        "profile_text": query[3],
        "catchphrase": query[4],
        "user_media": media.get_user_media(query[0]),
        "staff_notes": shout.count_staff_notes(query[0]),
    }


def removeavatar(userid, otherid):
    avatar.upload(otherid, None)
    note_about(userid, otherid, 'Avatar was removed.')


def removebanner(userid, otherid):
    banner.upload(otherid, None)
    note_about(userid, otherid, 'Banner was removed.')


def removecoverart(userid, submitid):
    sub = Submission.query.get(submitid)
    if not sub.cover_media:
        raise WeasylError("noCover")
    submission.reupload_cover(userid, submitid, None)
    otherid = sub.owner.userid
    title = sub.title

    note_about(userid, otherid, 'Cover was removed for ' +
               text.markdown_link(title, '/submission/%s?anyway=true' % submitid))


def removethumbnail(userid, submitid):
    sub = Submission.query.get(submitid)
    thumbnail.clear_thumbnail(userid, submitid)
    # Thumbnails may be cached on the front page, so invalidate that cache.
    index.recent_submissions.invalidate()
    submission.select_critique.invalidate(userid)
    otherid = sub.owner.userid
    title = sub.title
    note_about(userid, otherid, 'Thumbnail was removed for ' +
               text.markdown_link(title, '/submission/%s?anyway=true' % submitid))


def editprofiletext(userid, otherid, content):
    pr = d.meta.tables['profile']
    db = d.connect()
    condition = pr.c.userid == otherid
    previous_profile = db.scalar(sa.select([pr.c.profile_text]).where(condition))
    db.execute(pr.update().where(condition).values(profile_text=content))
    note_about(
        userid, otherid,
        'Profile text replaced with:',
        '%s\n\n## Profile text was:\n\n%s' % (content, previous_profile))


def editcatchphrase(userid, otherid, content):
    pr = d.meta.tables['profile']
    db = d.connect()
    condition = pr.c.userid == otherid
    previous_catchphrase = db.scalar(sa.select([pr.c.catchphrase]).where(condition))
    db.execute(pr.update().where(condition).values(catchphrase=content))
    note_about(
        userid, otherid,
        'Catchphrase replaced with:',
        '%s\n\n## Catchphrase was:\n\n%s' % (content, previous_catchphrase))


_tables = [
    (d.meta.tables['submission'], 'submitid', 'title', 'submission'),
    (d.meta.tables['character'], 'charid', 'char_name', 'character'),
    (d.meta.tables['journal'], 'journalid', 'title', 'journal'),
]


def bulk_edit_rating(userid, new_rating, submissions=(), characters=(), journals=()):
    action_string = 'rerated to ' + ratings.CODE_TO_NAME[new_rating]

    with d.engine.begin() as db:
        affected = collections.defaultdict(list)
        copyable = []

        for (tbl, pk, title_col, urlpart), ids in zip(_tables, [submissions, characters, journals]):
            if not ids:
                continue

            join = (
                tbl.select()
                .where(tbl.c[pk].in_(ids))
                .where(tbl.c.rating != new_rating)
                .with_for_update()
                .alias('join'))

            results = db.execute(
                tbl.update()
                .where(tbl.c[pk] == join.c[pk])
                .values(rating=new_rating)
                .returning(tbl.c[pk], tbl.c[title_col], tbl.c.userid, join.c.rating))

            for thingid, title, ownerid, original_rating in results:
                item_format = '- (from %s) %%s' % (original_rating.name,)
                affected[ownerid].append(item_format % text.markdown_link(title, '/%s/%s?anyway=true' % (urlpart, thingid)))
                copyable.append(item_format % text.markdown_link(title, '/%s/%s' % (urlpart, thingid)))

        now = arrow.utcnow()
        values = []
        for target, target_affected in affected.items():
            staff_note = '## The following items were %s:\n\n%s' % (action_string, '\n'.join(target_affected))
            values.append({
                'userid': userid,
                'target_user': target,
                'unixtime': now,
                'settings': 's',
                'content': staff_note,
            })
        if values:
            db.execute(d.meta.tables['comments'].insert().values(values))

    return 'Affected items (%s): \n\n%s' % (action_string, '\n'.join(copyable))


def bulk_edit(
    userid: int,
    *,
    action: str,
    submissions: list[int],
    characters: list[int],
    journals: list[int],
) -> str:
    if not submissions and not characters and not journals or action == 'null':
        return 'Nothing to do.'

    if action == 'show':
        # Unhide (show/make visible) a submission
        def action(tbl):
            return (
                tbl.update()
                .values(hidden=False)
                .where(tbl.c.hidden))

        action_string = 'unhidden'
        provide_link = True

    elif action == 'hide':
        # Hide a submission from public view
        def action(tbl):
            return (
                tbl.update()
                .values(hidden=True)
                .where(~tbl.c.hidden))

        action_string = 'hidden'
        # There's no value in giving the user a link to the submission as they
        # won't be able to see it.
        provide_link = False

    elif action.startswith('rate-'):
        # Re-rate a submission
        _, _, rating = action.partition('-')
        rating = int(rating)

        return bulk_edit_rating(userid, rating, submissions, characters, journals)

    elif action == 'clearcritique':
        # Clear the "critique requested" flag
        def action(tbl):
            return (
                tbl.update()
                .values(critique=False)
                .where(tbl.c.critique))

        action_string = 'unmarked as "critique requested"'
        provide_link = True

    elif action == 'setcritique':
        # Set the "critique requested" flag
        def action(tbl):
            return (
                tbl.update()
                .values(critique=True)
                .where(~tbl.c.critique))

        action_string = 'marked as "critique requested"'
        provide_link = True

    else:  # pragma: no cover
        raise WeasylError('Unexpected')

    db = d.connect()
    affected = collections.defaultdict(list)
    copyable = []

    for (tbl, col, title_col, urlpart), values in zip(_tables, [submissions, characters, journals]):
        if values:
            results = db.execute(
                action(tbl)
                .where(tbl.c[col].in_(values))
                .returning(tbl.c[col], tbl.c[title_col], tbl.c.userid))
            for thingid, title, ownerid in results:
                affected[ownerid].append('- ' + text.markdown_link(title, '/%s/%s?anyway=true' % (urlpart, thingid)))
                if provide_link:
                    copyable.append('- ' + text.markdown_link(title, '/%s/%s' % (urlpart, thingid)))
                else:
                    copyable.append('- %s' % (title,))

    cached_posts_count_invalidate_userids = list(affected.keys())
    if submissions:
        # bulk add collectors; see `weasyl.collection.find_owners`
        cached_posts_count_invalidate_userids.extend(
            row.userid
            for row in d.engine.execute(
                "SELECT DISTINCT userid FROM collection WHERE submitid = ANY (%(submissions)s) AND settings !~ '[pr]'",
                submissions=submissions,
            )
        )
    d.cached_posts_count_invalidate_multi(cached_posts_count_invalidate_userids)

    now = arrow.utcnow()
    values = []
    for target, target_affected in affected.items():
        staff_note = '## The following items were %s:\n\n%s' % (action_string, '\n'.join(target_affected))
        values.append({
            'userid': userid,
            'target_user': target,
            'unixtime': now,
            'settings': 's',
            'content': staff_note,
        })
    if values:
        db.execute(d.meta.tables['comments'].insert().values(values))

    return 'Affected items (%s): \n\n%s' % (action_string, '\n'.join(copyable))


def note_about(userid, target_user, title, message=None):
    staff_note = '## ' + title
    if message:
        staff_note = '%s\n\n%s' % (staff_note, message)

    db = d.connect()
    db.execute(
        d.meta.tables['comments'].insert()
        .values(
            userid=userid, target_user=target_user, unixtime=arrow.utcnow(),
            settings='s', content=staff_note,
        ))

from __future__ import absolute_import

import collections
import datetime

import arrow
import sqlalchemy as sa

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
from weasyl import welcome
from weasyl.error import WeasylError


BAN_TEMPLATES = {
    "01-incorrect-rating": {
        "name": "Incorrect Rating (3 Day Suspension)",
        "reason": (
            "Your account has been suspended for 3 days for repeated incorrect rating "
            "of submissions.\n\nYou may wish to review our "
            "[Ratings Guidelines](https://www.weasyl.com/help/ratings) during this time. "),
        "days": 3,
    },
    "02-incorrect-tag": {
        "name": "Incorrect Tags - Creator (3 Day Suspension)",
        "reason": (
            "Your account has been suspended for 3 days for repeated incorrect tagging "
            "of submissions.\n\nYou may wish to review our "
            "[Tagging Guide](https://www.weasyl.com/help/tagging) during this time."),
        "days": 3,
    },
    "03-byfor-14": {
        "name": "Right to Submit (14 Day Suspension)",
        "reason": (
            "Your account has been suspended for 14 days for repeatedly uploading "
            "content you do not have permission to upload.\n\nThis is a final warning - any "
            "further removals of submissions for this reason will result in a permanent ban "
            "from Weasyl. "),
        "days": 14,
    },
    "04-byfor": {
        "name": "Right to Submit (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly uploading content "
            "you do not have permission to upload. "),
        "days": -1,
    },
    "05-epilepsy-7": {
        "name": "Seizure Inducing Images (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for repeatedly uploading images "
            "in violation of Section I.C.4 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Seizure-Inducing Images:** Do not upload any avatars, banners, "
            "profile images, or submissions that feature rapidly flashing lights, colors, or "
            "rapid movement, as this may induce seizures in some users.\n\nThis is a final "
            "warning - any further removals of submissions for this reason will result in a "
            "permanent ban from Weasyl. "),
        "days": 7,
    },
    "06-epilepsy": {
        "name": "Seizure Inducing Images (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly uploading images "
            "in violation of Section I.C.4 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Seizure-Inducing Images:** Do not upload any avatars, banners, "
            "profile images, or submissions that feature rapidly flashing lights, colors, or "
            "rapid movement, as this may induce seizures in some users. "),
        "days": -1,
    },
    "07-offensive-3": {
        "name": "Offensive Material (3 Day Suspension)",
        "reason": (
            "Your account has been suspended for 3 days for uploading content in "
            "violation of Section I.C.1 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Offensive Content:** Submissions should avoid expressing bigoted "
            "or hateful material (e.g. racist, sexist, homophobic, etc.) to the extent "
            "possible without compromising the artistic integrity of the piece. Material that "
            "appears intended for the sole purpose of provoking hostile responses is not "
            "permitted. "),
        "days": 3,
    },
    "08-offensive-7": {
        "name": "Offensive Material (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for repeatedly uploading "
            "content in violation of Section I.C.1 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Offensive Content:** Submissions should avoid expressing bigoted "
            "or hateful material (e.g. racist, sexist, homophobic, etc.) to the extent "
            "possible without compromising the artistic integrity of the piece. Material that "
            "appears intended for the sole purpose of provoking hostile responses is not "
            "permitted.\n\nThis is a final warning - any further removals of submissions for "
            "this reason will result in a permanent ban from Weasyl. "),
        "days": 7,
    },
    "09-offensive": {
        "name": "Offensive Material (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly uploading content "
            "in violation of Section I.C.1 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Offensive Content:** Submissions should avoid expressing bigoted "
            "or hateful material (e.g. racist, sexist, homophobic, etc.) to the extent "
            "possible without compromising the artistic integrity of the piece. Material that "
            "appears intended for the sole purpose of provoking hostile responses is not "
            "permitted."),
        "days": -1,
    },
    "10-cp-14": {
        "name": "Minors In Mature Situations (14 Day Suspension)",
        "reason": (
            "Your account has been suspended for 14 days for repeatedly uploading "
            "content in violation of Section I.C.2 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which prohibits uploading "
            "content containing minors in mature/sexual situations.\n\nThis is a final "
            "warning - any further removals of submissions for this reason will result in a "
            "permanent ban from Weasyl. "),
        "days": 14,
    },
    "11-cp": {
        "name": "Minors In Mature Situations (Ban)",
        "reason": (
            "Your account has been banned from Weasyl for repeatedly uploading content "
            "in violation of Section I.C.2 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which prohibits uploading "
            "content containing minors in mature/sexual situations. "),
        "days": -1,
    },
    "12-theft-7": {
        "name": "Plagiarism - Single Submission (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for uploading content in "
            "violation of Section I.A.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Tracing and Plagiarism:** You may incorporate the work of others "
            "into new works; however, the use of borrowed content must either abide by fair "
            "use or you must obtain permission from the copyright holder. The submission will "
            "be removed if it meets neither of these requirements. If it does meet these "
            "requirements, you must still cite the content's source in the submission "
            "description.\n\nThis is a final warning - any further removals of submissions "
            "for this reason will result in a permanent ban from Weasyl. "),
        "days": 7,
    },
    "13-theft-14": {
        "name": "Plagiarism - Multiple Submissions (14 Day Suspension)",
        "reason": (
            "Your account has been suspended for 14 days for uploading content in "
            "violation of Section I.A.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Tracing and Plagiarism:** You may incorporate the work of others "
            "into new works; however, the use of borrowed content must either abide by fair "
            "use or you must obtain permission from the copyright holder. The submission will "
            "be removed if it meets neither of these requirements. If it does meet these "
            "requirements, you must still cite the content's source in the submission "
            "description.\n\nThis is a final warning - any further removals of submissions "
            "for this reason will result in a permanent ban from Weasyl. "),
        "days": 14,
    },
    "14-theft": {
        "name": "Plagiarism (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly uploading content "
            "in violation of Section I.A.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Tracing and Plagiarism:** You may incorporate the work of others "
            "into new works; however, the use of borrowed content must either abide by fair "
            "use or you must obtain permission from the copyright holder. The submission will "
            "be removed if it meets neither of these requirements. If it does meet these "
            "requirements, you must still cite the content's source in the submission "
            "description. "),
        "days": -1,
    },
    "15-tracing-single-3": {
        "name": "Tracing - Single Submission (3 Day Suspension)",
        "reason": (
            "Your account has been suspended for 3 days for uploading content in "
            "violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. "),
        "days": 3,
    },
    "16-tracing-single-7": {
        "name": "Tracing - Single Submission (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for repeatedly uploading "
            "content in violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. \n\nThis is a final "
            "warning - any further removals of submissions for this reason will result in a "
            "permanent ban from Weasyl. "),
        "days": 7,
    },
    "17-tracing-multiple-7": {
        "name": "Tracing - Multiple Submissions (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for uploading content in "
            "violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. \n\nThis is a final "
            "warning - any further removals of submissions for this reason will result in a "
            "permanent ban from Weasyl. "),
        "days": 7,
    },
    "18-tracing": {
        "name": "Tracing (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly "
            "uploading content in violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. "),
        "days": -1,
    },
    "19-eyeball-7": {
        "name": "Eyeballing (7 Day Suspension)",
        "reason": (
            "Your account has been suspended for 7 days for repeatedly uploading "
            "content in violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. \n\nThis is a final "
            "warning - any further removals of submissions for this reason will result in a "
            "permanent ban from Weasyl. "),
        "days": 7,
    },
    "20-eyeball": {
        "name": "Eyeballing (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for repeatedly "
            "uploading content in violation of Section I.C.3 of the [Community "
            "Guidelines](https://www.weasyl.com/policy/community), which states the "
            "following:\n> **Stolen Work:** Whether the work is traced, incorporates others' "
            "work, or outright plagiarizes, stealing others' work and either making it a part "
            "of your own submission without their permission or claiming it as your own is "
            "strictly forbidden. If another person has contributed to the submission in any "
            "way, they should receive credit for their participation. "),
        "days": -1,
    },
    "21-spammer": {
        "name": "Spam (Ban)",
        "reason": (
            "Your account has been permanently banned from Weasyl for spam."),
        "days": -1,
    },
}


def get_ban_reason(userid):
    return d.engine.scalar("SELECT reason FROM permaban WHERE userid = %(user)s",
                           user=userid)


def get_suspension(userid):
    return d.engine.execute("SELECT reason, release FROM suspension WHERE userid = %(user)s",
                            user=userid).first()


def finduser(userid, form):
    form.userid = d.get_int(form.userid)

    # If we don't have any of these variables, nothing will be displayed. So fast-return an empty list.
    if not form.userid and not form.username and not form.email and not form.dateafter \
            and not form.datebefore and not form.excludesuspended and not form.excludebanned \
            and not form.excludeactive and not form.ipaddr:
        return []

    lo = d.meta.tables['login']
    sh = d.meta.tables['comments']
    pr = d.meta.tables['profile']
    sess = d.meta.tables['sessions']

    q = d.sa.select([
        lo.c.userid,
        lo.c.login_name,
        lo.c.email,
        (d.sa.select([d.sa.func.count()])
         .select_from(sh)
         .where(sh.c.target_user == lo.c.userid)
         .where(sh.c.settings.op('~')('s'))).label('staff_notes'),
        lo.c.settings,
        lo.c.ip_address_at_signup,
        (d.sa.select([sess.c.ip_address])
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

    if form.userid:
        q = q.where(lo.c.userid == form.userid)
    elif form.username:
        q = q.where(lo.c.login_name.op('~')(form.username))
    elif form.email:
        q = q.where(d.sa.or_(
            lo.c.email.op('~')(form.email),
            lo.c.email.op('ilike')('%%%s%%' % form.email),
        ))

    # Filter for banned and/or suspended accounts
    if form.excludeactive == "on":
        q = q.where(lo.c.settings.op('~')('[bs]'))
    if form.excludebanned == "on":
        q = q.where(lo.c.settings.op('!~')('b'))
    if form.excludesuspended == "on":
        q = q.where(lo.c.settings.op('!~')('s'))

    # Filter for IP address
    if form.ipaddr:
        q = q.where(d.sa.or_(
            lo.c.ip_address_at_signup.op('ilike')('%s%%' % form.ipaddr),
            sess.c.ip_address.op('ilike')('%s%%' % form.ipaddr)
        ))

    # Filter for date-time
    if form.dateafter and form.datebefore:
        q = q.where(d.sa.between(pr.c.unixtime, arrow.get(form.dateafter), arrow.get(form.datebefore)))
    elif form.dateafter:
        q = q.where(pr.c.unixtime >= arrow.get(form.dateafter))
    elif form.datebefore:
        q = q.where(pr.c.unixtime <= arrow.get(form.datebefore))

    # Apply any row offset
    if form.row_offset:
        q = q.offset(form.row_offset)

    q = q.limit(250).order_by(lo.c.login_name.asc())
    db = d.connect()
    return db.execute(q)


# form
#   mode        reason
#   userid      release
#   username

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
        if form.datetype == "r":
            # Relative date
            magnitude = int(form.duration)

            if magnitude < 0:
                raise WeasylError("releaseInvalid")

            basedate = datetime.datetime.now()
            if form.durationunit == "y":
                basedate += datetime.timedelta(days=magnitude * 365)
            elif form.durationunit == "m":
                basedate += datetime.timedelta(days=magnitude * 30)
            elif form.durationunit == "w":
                basedate += datetime.timedelta(weeks=magnitude)
            else:  # Catchall, days
                basedate += datetime.timedelta(days=magnitude)

            form.release = d.convert_unixdate(basedate.day, basedate.month, basedate.year)
        else:
            # Absolute date
            if datetime.date(int(form.year), int(form.month), int(form.day)) < datetime.date.today():
                raise WeasylError("releaseInvalid")

            form.release = d.convert_unixdate(form.day, form.month, form.year)
    else:
        form.release = None

    if userid not in staff.MODS:
        raise WeasylError("Unexpected")
    elif form.userid in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    if form.mode == "b":
        query = d.engine.execute(
            "UPDATE login SET settings = REPLACE(REPLACE(settings, 'b', ''), 's', '') || 'b' WHERE userid = %(target)s",
            target=form.userid)

        if query.rowcount != 1:
            raise WeasylError("Unexpected")

        d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
        d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)
        d.engine.execute("INSERT INTO permaban VALUES (%(target)s, %(reason)s)", target=form.userid, reason=form.reason)
    elif form.mode == "s":
        if not form.release:
            raise WeasylError("releaseInvalid")

        query = d.engine.execute(
            "UPDATE login SET settings = REPLACE(REPLACE(settings, 'b', ''), 's', '') || 's' WHERE userid = %(target)s",
            target=form.userid)

        if query.rowcount != 1:
            raise WeasylError("Unexpected")

        d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
        d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)
        d.engine.execute("INSERT INTO suspension VALUES (%(target)s, %(reason)s, %(release)s)", target=form.userid, reason=form.reason, release=form.release)
    elif form.mode == "x":
        query = d.engine.execute(
            "UPDATE login SET settings = REPLACE(REPLACE(settings, 's', ''), 'b', '') WHERE userid = %(target)s",
            target=form.userid)

        if query.rowcount != 1:
            raise WeasylError("Unexpected")

        d.engine.execute("DELETE FROM permaban WHERE userid = %(target)s", target=form.userid)
        d.engine.execute("DELETE FROM suspension WHERE userid = %(target)s", target=form.userid)

    action = _mode_to_action_map.get(form.mode)
    if action is not None:
        isoformat_release = None
        message = form.reason
        if form.release is not None:
            isoformat_release = d.datetime.datetime.fromtimestamp(form.release).isoformat()
            message = '#### Release date: %s\n\n%s' % (isoformat_release, message)
        d.append_to_log(
            'staff.actions',
            userid=userid, action=action, target=form.userid, reason=form.reason,
            release=isoformat_release)
        d._get_all_config.invalidate(form.userid)
        note_about(userid, form.userid, 'User mode changed: action was %r' % (action,), message)


def submissionsbyuser(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    query = d.engine.execute("""
        SELECT su.submitid, su.title, su.rating, su.unixtime, su.userid, pr.username, su.settings
        FROM submission su
            INNER JOIN profile pr USING (userid)
        WHERE su.userid = (SELECT userid FROM login WHERE login_name = %(sysname)s)
        ORDER BY su.submitid DESC
    """, sysname=d.get_sysname(form.name))

    ret = [{
        "contype": 10,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "settings": i[6],
    } for i in query]
    media.populate_with_submission_media(ret)
    return ret


def charactersbyuser(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    query = d.engine.execute("""
        SELECT
            ch.charid, pr.username, ch.unixtime,
            ch.char_name, ch.age, ch.gender, ch.height, ch.weight, ch.species,
            ch.content, ch.rating, ch.settings, ch.page_views, pr.config
        FROM character ch
        INNER JOIN profile pr ON ch.userid = pr.userid
        INNER JOIN login ON ch.userid = login.userid
        WHERE login.login_name = %(sysname)s
    """, sysname=d.get_sysname(form.name))

    return [{
        "contype": 20,
        "userid": userid,
        "charid": item[0],
        "username": item[1],
        "unixtime": item[2],
        "title": item[3],
        "rating": item[10],
        "settings": item[11],
        "sub_media": character.fake_media_items(item[0], userid, d.get_sysname(item[1]), item[11]),
    } for item in query]


def journalsbyuser(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    results = d.engine.execute("""
        SELECT journalid, title, journal.settings, journal.unixtime, rating,
               profile.username, 30 contype
          FROM journal
               JOIN profile USING (userid)
               JOIN login USING (userid)
         WHERE login_name = %(sysname)s
    """, sysname=d.get_sysname(form.name)).fetchall()

    return map(dict, results)


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


def hidesubmission(submitid):
    d.execute("UPDATE submission SET settings = settings || 'h' WHERE submitid = %i AND settings !~ 'h'", [submitid])
    welcome.submission_remove(submitid)


def unhidesubmission(submitid):
    d.execute("UPDATE submission SET settings = REPLACE(settings, 'h', '') WHERE submitid = %i", [submitid])


def hidecharacter(charid):
    d.execute("UPDATE character SET settings = settings || 'h' WHERE charid = %i AND settings !~ 'h'", [charid])
    welcome.character_remove(charid)


def unhidecharacter(charid):
    d.execute("UPDATE character SET settings = REPLACE(settings, 'h', '') WHERE charid = %i", [charid])


def hidejournal(journalid):
    """ Hides a journal item from view, and removes it from the welcome table. """
    d.engine.execute("""
        UPDATE journal
        SET settings = settings || 'h'
        WHERE journalid = %(journalid)s
            AND settings !~ 'h'
    """, journalid=journalid)
    welcome.journal_remove(journalid=journalid)


def unhidejournal(journalid):
    """ Removes the hidden settings flag from a journal item, restoring it to view if other conditions are met (e.g., not flagged as spam) """
    d.engine.execute("""
        UPDATE journal
        SET settings = REPLACE(settings, 'h', '')
        WHERE journalid = %(journalid)s
    """, journalid=journalid)


def manageuser(userid, form):
    if userid not in staff.MODS:
        raise WeasylError("Unexpected")

    query = d.engine.execute(
        "SELECT userid, username, config, profile_text, catchphrase FROM profile"
        " WHERE userid = (SELECT userid FROM login WHERE login_name = %(name)s)",
        name=d.get_sysname(form.name),
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
        "staff_notes": shout.count(query[0], staffnotes=True),
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
    index.template_fields.invalidate(userid)
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
        for target, target_affected in affected.iteritems():
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


def bulk_edit(userid, action, submissions=(), characters=(), journals=()):
    if not submissions and not characters and not journals or action == 'null':
        return 'Nothing to do.'

    if action == 'show':
        # Unhide (show/make visible) a submission
        def action(tbl):
            return (
                tbl.update()
                .values(settings=sa.func.replace(tbl.c.settings, 'h', ''))
                .where(tbl.c.settings.op('~')('h')))
        action_string = 'unhidden'
        provide_link = True

    elif action == 'hide':
        # Hide a submission from public view
        def action(tbl):
            return (
                tbl.update()
                .values(settings=tbl.c.settings.op('||')('h'))
                .where(tbl.c.settings.op('!~')('h')))
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
                .values(settings=sa.func.replace(tbl.c.settings, 'q', ''))
                .where(tbl.c.settings.op('~')('q')))
        action_string = 'unmarked as "critique requested"'
        provide_link = True

    elif action == 'setcritique':
        # Set the "critique requested" flag
        def action(tbl):
            return (
                tbl.update()
                .values(settings=tbl.c.settings.op('||')('q'))
                .where(tbl.c.settings.op('!~')('q')))
        action_string = 'marked as "critique requested"'
        provide_link = True

    else:
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

    now = arrow.utcnow()
    values = []
    for target, target_affected in affected.iteritems():
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

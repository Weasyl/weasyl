from __future__ import absolute_import

import pytz
import sqlalchemy as sa
from translationstring import TranslationString as _

from libweasyl import ratings
from libweasyl import security
from libweasyl import staff
from libweasyl.cache import region
from libweasyl.html import strip_html
from libweasyl.models import tables

from weasyl import define as d
from weasyl import emailer
from weasyl import macro as m
from weasyl import media
from weasyl import orm
from weasyl import shout
from weasyl import welcome
from weasyl.configuration_builder import create_configuration, BoolOption, ConfigOption
from weasyl.error import WeasylError


class ExchangeType:
    def __init__(self, name_singular, name_plural):
        self.name_singular = name_singular
        self.name_plural = name_plural


EXCHANGE_TYPE_TRADE = ExchangeType("trade", "trades")
EXCHANGE_TYPE_REQUEST = ExchangeType("request", "requests")
EXCHANGE_TYPE_COMMISSION = ExchangeType("commission", "commissions")


class ExchangeSetting:
    def __init__(self, code, text):
        self.code = code
        self.text = text

    def format(self, request_type):
        return _(self.text.format(type=request_type))


EXCHANGE_SETTING_ACCEPTING = ExchangeSetting("o", "I am currently accepting {type.name_plural}")
EXCHANGE_SETTING_SOMETIMES = ExchangeSetting("s", "I may sometimes accept {type.name_plural}")
EXCHANGE_SETTING_FULL_QUEUE = ExchangeSetting("f", "My {type.name_singular} queue is currently filled")
EXCHANGE_SETTING_NOT_ACCEPTING = ExchangeSetting("c", "I am not accepting {type.name_plural} right now")
EXCHANGE_SETTING_NOT_APPLICABLE = ExchangeSetting("e", "This is not applicable to me")

ALL_EXCHANGE_SETTINGS = [EXCHANGE_SETTING_ACCEPTING, EXCHANGE_SETTING_SOMETIMES,
                         EXCHANGE_SETTING_FULL_QUEUE, EXCHANGE_SETTING_NOT_ACCEPTING,
                         EXCHANGE_SETTING_NOT_APPLICABLE]
EXCHANGE_SETTING_CODE_MAP = {setting.code: setting for setting in ALL_EXCHANGE_SETTINGS}

ALLOWABLE_EXCHANGE_CODES = {
    EXCHANGE_TYPE_TRADE: 'osce',
    EXCHANGE_TYPE_REQUEST: 'osce',
    EXCHANGE_TYPE_COMMISSION: 'osfce',
}


Config = create_configuration([
    BoolOption("twelvehour", "2"),
    ConfigOption("rating", dict(zip(ratings.ALL_RATINGS, ["", "a", "p"]))),
    BoolOption("tagging", "k"),
    BoolOption("hideprofile", "h"),
    BoolOption("hidestats", "i"),
    BoolOption("hidefavorites", "v"),
    BoolOption("hidefavbar", "u"),
    ConfigOption("shouts", {"anyone": "", "friends_only": "x", "staff_only": "w"}),
    ConfigOption("notes", {"anyone": "", "friends_only": "z", "staff_only": "y"}),
    BoolOption("filter", "l"),
    BoolOption("follow_s", "s"),
    BoolOption("follow_c", "c"),
    BoolOption("follow_f", "f"),
    BoolOption("follow_t", "t"),
    BoolOption("follow_j", "j"),
])


def get_exchange_setting(exchange_type, code):
    if code not in ALLOWABLE_EXCHANGE_CODES[exchange_type]:
        return EXCHANGE_SETTING_NOT_ACCEPTING
    return EXCHANGE_SETTING_CODE_MAP[code]


def exchange_settings_from_settings_string(settings_string):
    """
    Given a (terrible and brittle) exchange settings string from a user profile,
    returns a dict of their exchange settings.
    """
    return {
        EXCHANGE_TYPE_COMMISSION: EXCHANGE_SETTING_CODE_MAP[settings_string[0]],
        EXCHANGE_TYPE_TRADE: EXCHANGE_SETTING_CODE_MAP[settings_string[1]],
        EXCHANGE_TYPE_REQUEST: EXCHANGE_SETTING_CODE_MAP[settings_string[2]],
    }


def resolve(userid, otherid, othername, myself=True):
    """
    Attempts to determine the userid of a specified user; resolves using otherid,
    othername, and userid (if myself is True), in that order. If no userid can be
    resolved, returns 0 instead.
    """
    result = None

    if otherid:
        result = d.engine.scalar("SELECT userid FROM login WHERE userid = %(id)s", id=d.get_int(otherid))

        if result:
            return result
    elif othername:
        result = d.engine.scalar("SELECT userid FROM login WHERE login_name = %(name)s", name=d.get_sysname(othername))

        if result:
            return result

        result = d.engine.scalar("SELECT userid FROM useralias WHERE alias_name = %(name)s", name=d.get_sysname(othername))

        if result:
            return result
    elif userid and myself:
        return userid

    return 0


@region.cache_on_arguments()
@d.record_timing
def resolve_by_login(login):
    return resolve(None, None, login, False)


def select_profile(userid, avatar=False, banner=False, propic=False, images=False, commish=True, viewer=None):
    query = d.engine.execute("""
        SELECT pr.username, pr.full_name, pr.catchphrase, pr.unixtime, pr.profile_text,
            pr.settings, pr.stream_url, pr.config, pr.stream_text, lo.settings, us.end_time
        FROM profile pr
            INNER JOIN login lo USING (userid)
            LEFT JOIN user_streams us USING (userid)
        WHERE userid = %(user)s
    """, user=userid).first()

    if not query:
        raise WeasylError('RecordMissing')

    streaming_status = "stopped"
    if query[6]:  # profile.stream_url
        if query[10] > d.get_time():  # user_streams.end_time
            streaming_status = "started"
        elif 'l' in query[5]:
            streaming_status = "later"

    return {
        "userid": userid,
        "user_media": media.get_user_media(userid),
        "username": query[0],
        "full_name": query[1],
        "catchphrase": query[2],
        "unixtime": query[3],
        "profile_text": query[4],
        "settings": query[5],
        "stream_url": query[6],
        "stream_text": query[8],
        "config": query[7],
        "show_favorites_bar": "u" not in query[7] and "v" not in query[7],
        "show_favorites_tab": userid == viewer or "v" not in query[7],
        "commish_slots": 0,
        "banned": "b" in query[9],
        "suspended": "s" in query[9],
        "streaming_status": streaming_status,
    }


def twitter_card(userid):
    username, full_name, catchphrase, profile_text, config, twitter = d.engine.execute(
        "SELECT pr.username, pr.full_name, pr.catchphrase, pr.profile_text, pr.config, ul.link_value "
        "FROM profile pr "
        "LEFT JOIN user_links ul ON pr.userid = ul.userid AND ul.link_type = 'twitter' "
        "WHERE pr.userid = %(user)s",
        user=userid).first()

    ret = {
        'card': 'summary',
        'url': d.absolutify_url('/~%s' % (username,)),
        'title': '%s on Weasyl' % (full_name,),
    }

    if catchphrase:
        description = '"%s"' % (catchphrase,)
    elif profile_text:
        description = strip_html(profile_text)
    else:
        description = "[%s has an empty profile, but is eggcelent!]" % (full_name,)
    ret['description'] = d.summarize(description)

    media_items = media.get_user_media(userid)
    ret['image:src'] = d.absolutify_url(media_items['avatar'][0]['display_url'])

    if twitter:
        ret['creator'] = '@%s' % (twitter.lstrip('@'),)

    return ret


def select_myself(userid):
    if not userid:
        return None

    return {
        "userid": userid,
        "username": d.get_display_name(userid),
        "is_mod": userid in staff.MODS,
        "is_verified": d.is_vouched_for(userid),
        "user_media": media.get_user_media(userid),
    }


def get_user_age(userid):
    assert userid
    return d.convert_age(d.engine.scalar("SELECT birthday FROM userinfo WHERE userid = %(user)s", user=userid))


def get_user_ratings(userid):
    return ratings.get_ratings_for_age(get_user_age(userid))


def check_user_rating_allowed(userid, rating):
    # TODO(kailys): ensure usages always pass a Rating
    minimum_age = rating.minimum_age if isinstance(rating, ratings.Rating) else ratings.CODE_MAP[rating].minimum_age
    if get_user_age(userid) < minimum_age:
        raise WeasylError("ratingInvalid")


def select_userinfo(userid, config=None):
    if config is None:
        query = tuple(d.engine.execute("""
            SELECT pr.config, ui.birthday, ui.gender, ui.country
            FROM profile pr
            INNER JOIN userinfo ui USING (userid)
            WHERE pr.userid = %(userid)s
        """, userid=userid).first())
    else:
        query = (config,) + tuple(d.engine.execute("""
            SELECT birthday, gender, country
            FROM userinfo
            WHERE userid = %(userid)s
        """, userid=userid).first())

    user_links = d.engine.execute("""
        SELECT link_type, ARRAY_AGG(link_value ORDER BY link_value)
        FROM user_links
        WHERE userid = %(userid)s
        GROUP BY link_type
    """, userid=userid).fetchall()

    show_age = "b" in query[0] or d.get_userid() in staff.MODS
    return {
        "birthday": query[1],
        "age": d.convert_age(query[1]) if show_age else None,
        "show_age": "b" in query[0],
        "gender": query[2],
        "country": query[3],
        "user_links": {r[0]: r[1] for r in user_links},
        "sorted_user_links": sort_user_links(user_links),
    }


def select_report_stats(userid):
    query_byreason = d.engine.execute("""
        SELECT count(r.reportid), r.closure_reason FROM report r
        JOIN reportcomment c ON r.reportid = c.reportid
        WHERE c.userid = %(userid)s AND r.closed_at IS NOT null
        GROUP BY r.closure_reason
        UNION
        SELECT count(r.reportid), r.closure_reason FROM report r
        JOIN reportcomment c ON r.reportid = c.reportid
        WHERE c.userid = %(userid)s AND r.closed_at IS null
        GROUP BY r.closure_reason
    """, userid=userid)
    # create a dict of {'closure_reason' : 'count'}
    # closure_reason will be None if report was not yet closed.
    return {row[1].replace("-", " ").title() if row[1] is not None else "Open":
            row[0] for row in query_byreason}


def select_relation(userid, otherid):
    if not userid or userid == otherid:
        return {
            "follow": False,
            "friend": False,
            "ignore": False,
            "friendreq": False,
            "follower": False,
            "is_self": userid == otherid,
        }

    query = d.engine.execute("""
        SELECT
            (SELECT EXISTS (SELECT 0 FROM watchuser WHERE (userid, otherid) = (%(user)s, %(other)s)) AS follow),
            (SELECT EXISTS (SELECT 0 FROM frienduser WHERE userid IN (%(user)s, %(other)s) AND otherid IN (%(user)s, %(other)s) AND settings !~ 'p') AS friend),
            (SELECT EXISTS (SELECT 0 FROM ignoreuser WHERE (userid, otherid) = (%(user)s, %(other)s)) AS ignore),
            (SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%(user)s, %(other)s) AND settings ~ 'p') AS friendreq),
            (SELECT EXISTS (SELECT 0 FROM watchuser WHERE (userid, otherid) = (%(other)s, %(user)s)) AS follower)
    """, user=userid, other=otherid).first()

    return dict(
        query,
        is_self=False)


@region.cache_on_arguments(expiration_time=600)
@d.record_timing
def _select_statistics(userid):
    query = d.engine.execute("""
        SELECT
            (SELECT page_views FROM profile WHERE userid = %(user)s),
            (SELECT COUNT(*) FROM favorite WHERE userid = %(user)s),
            (SELECT
                (SELECT COUNT(*) FROM favorite fa JOIN submission su ON fa.targetid = su.submitid
                    WHERE su.userid = %(user)s AND fa.type = 's') +
                (SELECT COUNT(*) FROM favorite fa JOIN character ch ON fa.targetid = ch.charid
                    WHERE ch.userid = %(user)s AND fa.type = 'f') +
                (SELECT COUNT(*) FROM favorite fa JOIN journal jo ON fa.targetid = jo.journalid
                    WHERE jo.userid = %(user)s AND fa.type = 'j')),
            (SELECT COUNT(*) FROM watchuser WHERE otherid = %(user)s),
            (SELECT COUNT(*) FROM watchuser WHERE userid = %(user)s),
            (SELECT COUNT(*) FROM submission WHERE userid = %(user)s AND settings !~ 'h'),
            (SELECT COUNT(*) FROM journal WHERE userid = %(user)s AND settings !~ 'h'),
            (SELECT COUNT(*) FROM comments WHERE target_user = %(user)s AND settings !~ 'h' AND settings ~ 's')
    """, user=userid).first()

    return {
        "page_views": query[0],
        "submit_views": 0,
        "faves_sent": query[1],
        "faves_received": query[2],
        "followed": query[3],
        "following": query[4],
        "submissions": query[5],
        "journals": query[6],
        "staff_notes": query[7],
    }


def select_statistics(userid):
    show = "i" not in d.get_config(userid) or d.get_userid() in staff.MODS
    return _select_statistics(userid), show


def select_streaming(userid, rating, limit, following=True, order_by=None):
    statement = [
        "SELECT userid, pr.username, pr.stream_url, pr.config, pr.stream_text, start_time "
        "FROM profile pr "
        "JOIN user_streams USING (userid) "
        "JOIN login USING (userid) "
        "WHERE login.voucher IS NOT NULL AND end_time > %i" % (d.get_time(),)
    ]

    if userid:
        statement.append(m.MACRO_IGNOREUSER % (userid, "pr"))

        if following:
            pass  # todo
    if order_by:
        statement.append(" ORDER BY %s LIMIT %i" % (order_by, limit))
    else:
        statement.append(" ORDER BY RANDOM() LIMIT %i" % limit)

    ret = [{
        "userid": i[0],
        "username": i[1],
        "stream_url": i[2],
        "stream_text": i[4],
        "stream_time": i[5],
    } for i in d.execute("".join(statement)) if i[2]]

    media.populate_with_user_media(ret)
    return ret


def select_avatars(userids):
    if not userids:
        return {}

    results = d.engine.execute(
        'SELECT userid, username FROM profile WHERE userid = ANY (%(users)s)',
        users=userids)
    results = [dict(row) for row in results]
    media.populate_with_user_media(results)
    return {d['userid']: d for d in results}


def edit_profile_settings(userid,
                          set_trade=EXCHANGE_SETTING_NOT_ACCEPTING,
                          set_request=EXCHANGE_SETTING_NOT_ACCEPTING,
                          set_commission=EXCHANGE_SETTING_NOT_ACCEPTING):
    settings = "".join([set_commission.code, set_trade.code, set_request.code])
    d.engine.execute(
        "UPDATE profile SET settings = %(settings)s WHERE userid = %(user)s",
        settings=settings, user=userid)
    d._get_all_config.invalidate(userid)


def edit_profile(userid, profile,
                 set_trade=EXCHANGE_SETTING_NOT_ACCEPTING,
                 set_request=EXCHANGE_SETTING_NOT_ACCEPTING,
                 set_commission=EXCHANGE_SETTING_NOT_ACCEPTING,
                 profile_display=''):
    # Assign settings
    settings = "".join([set_commission.code, set_trade.code, set_request.code])

    if profile_display not in ('O', 'A'):
        profile_display = ''

    pr = d.meta.tables['profile']
    d.engine.execute(
        pr.update()
        .where(pr.c.userid == userid)
        .values({
            'full_name': profile.full_name,
            'catchphrase': profile.catchphrase,
            'profile_text': profile.profile_text,
            'settings': settings,
            'config': sa.func.regexp_replace(pr.c.config, "[OA]", "").concat(profile_display),
        })
    )
    d._get_all_config.invalidate(userid)


STREAMING_ACTION_MAP = {
    '': 'not streaming',
    'later': 'streaming later',
    'start': 'now streaming',
    'still': 'still streaming',
}


def edit_streaming_settings(my_userid, userid, profile, set_stream=None, stream_length=0):

    if set_stream == 'start':
        if stream_length < 1 or stream_length > 360:
            raise WeasylError("streamDurationOutOfRange")

        if not profile.stream_url:
            raise WeasylError("streamLocationNotSet")

    # unless we're specifically still streaming, clear the user_streams record
    if set_stream != 'still':
        d.execute("DELETE FROM user_streams WHERE userid = %i", [userid])

    settings_flag = ''
    stream_status = None
    # if we're starting to stream, update user_streams to reflect that
    if set_stream == 'start':
        now = d.get_time()
        stream_end = now + stream_length * 60  # stream_length is minutes; we need seconds
        d.execute("INSERT INTO user_streams VALUES (%i, %i, %i)", [userid, now, stream_end])
        stream_status = 'n'
    # if we're going to stream later, update profile.settings to reflect that
    elif set_stream == 'later':
        settings_flag = stream_status = 'l'

    # if stream_status is None, any rows in `welcome` will get cleared. but, if
    # the user is still streaming, that shouldn't happen. otherwise, `welcome`
    # will get updated with the current stream state.
    if set_stream != 'still':
        welcome.stream_insert(userid, stream_status)

    pr = d.meta.tables['profile']
    d.engine.execute(
        pr.update()
        .where(pr.c.userid == userid)
        .values({
            'stream_text': profile.stream_text,
            'stream_url': profile.stream_url,
            'settings': sa.func.regexp_replace(pr.c.settings, "[nli]", "").concat(settings_flag),
        })
    )

    if my_userid != userid:
        from weasyl import moderation
        note_body = (
            '- Stream url: %s\n'
            '- Stream description: %s\n'
            '- Stream status: %s' % (profile.stream_url, profile.stream_text, STREAMING_ACTION_MAP[set_stream]))
        moderation.note_about(my_userid, userid, 'Streaming settings updated:', note_body)


# form
#   show_age
#   gender
#   country
#   (...)

def edit_userinfo(userid, form):
    social_rows = []
    for site_name, site_value in zip(form.site_names, form.site_values):
        if not site_name or not site_value:
            continue
        row = {
            'userid': userid,
            'link_type': site_name,
            'link_value': site_value,
        }
        social_rows.append(row)

    d.engine.execute("""
        UPDATE userinfo
        SET gender = %(gender)s, country = %(country)s
        WHERE userid = %(userid)s
    """, userid=userid, gender=form.gender.strip(), country=form.country.strip())
    d.engine.execute("""
        DELETE FROM user_links
        WHERE userid = %(userid)s
    """, userid=userid)
    if social_rows:
        d.engine.execute(d.meta.tables['user_links'].insert().values(social_rows))

    if form.show_age:
        d.engine.execute("""
            UPDATE profile
            SET config = config || 'b'
            WHERE userid = %(userid)s
            AND config !~ 'b'
        """, userid=userid)
    else:
        d.engine.execute("""
            UPDATE profile
            SET config = REPLACE(config, 'b', '')
            WHERE userid = %(userid)s
        """, userid=userid)

    d._get_all_config.invalidate(userid)


def edit_email_password(userid, username, password, newemail, newemailcheck,
                        newpassword, newpasscheck):
    """
    Edit the email address and/or password for a given Weasyl account.

    After verifying the user's current login credentials, edit the user's email address and/or
    password if validity checks pass. If the email is modified, a confirmation email is sent
    to the user's target email with a token which, if used, finalizes the email address change.

    Parameters:
        userid: The `userid` of the Weasyl account to modify.
        username: User-entered username for password-based authentication.
        password: The user's current plaintext password.
        newemail: If changing the email on the account, the new email address. Optional.
        newemailcheck: A verification field for the above to serve as a typo-check. Optional,
        but mandatory if `newemail` provided.
        newpassword: If changing the password, the user's new password. Optional.
        newpasswordcheck: Verification field for `newpassword`. Optional, but mandatory if
        `newpassword` provided.
    """
    from weasyl import login

    # Track if any changes were made for later display back to the user.
    changes_made = ""

    # Check that credentials are correct
    logid, logerror = login.authenticate_bcrypt(username, password, request=None)

    # Run checks prior to modifying anything...
    if userid != logid or logerror is not None:
        raise WeasylError("loginInvalid")

    if newemail:
        if newemail != newemailcheck:
            raise WeasylError("emailMismatch")

    if newpassword:
        if newpassword != newpasscheck:
            raise WeasylError("passwordMismatch")
        elif not login.password_secure(newpassword):
            raise WeasylError("passwordInsecure")

    # If we are setting a new email, then write the email into a holding table pending confirmation
    #   that the email is valid.
    if newemail:
        # Only actually attempt to change the email if unused; prevent finding out if an email is already registered
        if not login.email_exists(newemail):
            token = security.generate_key(40)
            # Store the current token & email, updating them to overwrite a previous attempt if needed
            d.engine.execute("""
                INSERT INTO emailverify (userid, email, token, createtimestamp)
                VALUES (%(userid)s, %(newemail)s, %(token)s, NOW())
                ON CONFLICT (userid) DO
                  UPDATE SET email = %(newemail)s, token = %(token)s, createtimestamp = NOW()
            """, userid=userid, newemail=newemail, token=token)

            # Send out the email containing the verification token.
            emailer.send(newemail, "Weasyl Email Change Confirmation", d.render("email/verify_emailchange.html", [token, d.get_display_name(userid)]))
        else:
            # The target email exists: let the target know this
            query_username = d.engine.scalar("""
                SELECT login_name FROM login WHERE email = %(email)s
            """, email=newemail)
            emailer.send(newemail, "Weasyl Account Information - Duplicate Email on Accounts Rejected", d.render(
                "email/email_in_use_email_change.html", [query_username])
            )

        # Then add text to `changes_made` telling that we have completed the email change request, and how to proceed.
        changes_made += "Your email change request is currently pending. An email has been sent to **" + newemail + "**. Follow the instructions within to finalize your email address change.\n"

    # If the password is being updated, update the hash, and clear other sessions.
    if newpassword:
        d.engine.execute(
            "UPDATE authbcrypt SET hashsum = %(new_hash)s WHERE userid = %(user)s",
            new_hash=login.passhash(newpassword), user=userid)

        # Invalidate all sessions for `userid` except for the current one
        invalidate_other_sessions(userid)

        # Then add to `changes_made` detailing that the password change has successfully occurred.
        changes_made += "Your password has been successfully changed. As a security precaution, you have been logged out of all other active sessions."

    if changes_made != "":
        return changes_made
    else:
        return False


def invalidate_other_sessions(userid):
    """
    Invalidate all HTTP sessions for `userid` except for the current session.

    Useful as a security precaution, such as if a user changes their password, or enables
    2FA.

    Parameters:
        userid: The userid for the account to clear sessions from.

    Returns: Nothing.
    """
    sess = d.get_weasyl_session()
    d.engine.execute("""
        DELETE FROM sessions
        WHERE userid = %(userid)s
          AND sessionid != %(currentsession)s
    """, userid=userid, currentsession=sess.sessionid)


def edit_preferences(userid, timezone=None,
                     preferences=None, jsonb_settings=None):
    """
    Apply changes to stored preferences for a given user.
    :param userid: The userid to apply changes to
    :param timezone: (optional) new Timezone to set for user
    :param preferences: (optional) old-style char preferences, overwrites all previous settings
    :param jsonb_settings: (optional) JSON preferences, overwrites all previous settings
    :return: None
    """
    config = d.get_config(userid)

    tooyoung = False
    if preferences is not None:
        tooyoung |= get_user_age(userid) < preferences.rating.minimum_age
    if jsonb_settings is not None:
        sfwrating = jsonb_settings.max_sfw_rating
        sfwrating = ratings.CODE_MAP.get(sfwrating, ratings.GENERAL)
        tooyoung |= get_user_age(userid) < sfwrating.minimum_age

    if tooyoung:
        raise WeasylError("birthdayInsufficient")
    if timezone is not None and timezone not in pytz.all_timezones:
        raise WeasylError('invalidTimezone')

    db = d.connect()
    updates = {}
    if preferences is not None:
        # update legacy preferences
        # clear out the option codes that are being replaced.
        for i in Config.all_option_codes:
            config = config.replace(i, "")
        config_str = config + preferences.to_code()
        updates['config'] = config_str
        d._get_all_config.invalidate(userid)
    if jsonb_settings is not None:
        # update jsonb preferences
        updates['jsonb_settings'] = jsonb_settings.get_raw()
        d._get_profile_settings.invalidate(userid)

    d.engine.execute(
        tables.profile.update().where(tables.profile.c.userid == userid),
        updates
    )

    # update TZ
    if timezone is not None:
        tz = db.query(orm.UserTimezone).get(userid)
        if tz is None:
            tz = orm.UserTimezone(userid=userid)
            db.add(tz)
        tz.timezone = timezone
        db.flush()
        tz.cache()
    else:
        db.flush()


def select_manage(userid):
    """Selects a user's information for display in the admin user management page.

    Args:
        userid (int): ID of user to fetch information for.

    Returns:
        Relevant user information as a dict.
    """
    query = d.engine.execute("""
        SELECT
            lo.userid, lo.last_login, lo.email, lo.ip_address_at_signup,
            pr.unixtime, pr.username, pr.full_name, pr.catchphrase,
            ui.birthday, ui.gender, ui.country, pr.config
        FROM login lo
            INNER JOIN profile pr USING (userid)
            INNER JOIN userinfo ui USING (userid)
        WHERE lo.userid = %(user)s
    """, user=userid).first()

    if not query:
        raise WeasylError("Unexpected")

    user_link_rows = d.engine.execute("""
        SELECT link_type, ARRAY_AGG(link_value ORDER BY link_value)
        FROM user_links
        WHERE userid = %(userid)s
        GROUP BY link_type
    """, userid=userid)

    active_user_sessions = d.engine.execute("""
        SELECT sess.created_at, sess.ip_address, ua.user_agent
        FROM login lo
            INNER JOIN sessions sess ON lo.userid = sess.userid
            INNER JOIN user_agents ua ON sess.user_agent_id = ua.user_agent_id
        WHERE lo.userid = %(userid)s
        ORDER BY sess.created_at DESC
    """, userid=userid).fetchall()

    return {
        "userid": query[0],
        "last_login": query[1],
        "email": query[2],
        "ip_address_at_signup": query[3],
        "unixtime": query[4],
        "username": query[5],
        "full_name": query[6],
        "catchphrase": query[7],
        "birthday": query[8],
        "gender": query[9],
        "country": query[10],
        "config": query[11],
        "staff_notes": shout.count(userid, staffnotes=True),
        "sorted_user_links": sort_user_links(user_link_rows),
        "user_sessions": active_user_sessions,
    }


def do_manage(my_userid, userid, username=None, full_name=None, catchphrase=None,
              birthday=None, gender=None, country=None, remove_social=None,
              permission_tag=None):
    """Updates a user's information from the admin user management page.
    After updating the user it records all the changes into the mod notes.

    If an argument is None it will not be updated.

    Args:
        my_userid (int): ID of user making changes to other user.
        userid (int): ID of user to modify.
        username (str): New username for user. Defaults to None.
        full_name (str): New full name for user. Defaults to None.
        catchphrase (str): New catchphrase for user. Defaults to None.
        birthday (str): New birthday for user, in format for convert_inputdate. Defaults to None.
        gender (str): New gender for user. Defaults to None.
        country (str): New country for user. Defaults to None.
        remove_social (list): Items to remove from the user's social/contact links. Defaults to None.
        permission_tag (bool): New tagging permission for user. Defaults to None.

    Returns:
        Does not return.
    """
    updates = []

    # Username
    if username is not None:
        sysname = d.get_sysname(username)

        if not sysname:
            raise WeasylError("usernameInvalid")
        elif d.engine.scalar("SELECT EXISTS (SELECT 0 FROM login WHERE login_name = %(name)s)",
                             name=sysname):
            raise WeasylError("usernameExists")
        elif d.engine.scalar("SELECT EXISTS (SELECT 0 FROM useralias WHERE alias_name = %(name)s)",
                             name=sysname):
            raise WeasylError("usernameExists")
        elif d.engine.scalar("SELECT EXISTS (SELECT 0 FROM logincreate WHERE login_name = %(name)s)",
                             name=sysname):
            raise WeasylError("usernameExists")

        with d.engine.begin() as db:
            db.execute(
                "UPDATE login SET login_name = %(sysname)s WHERE userid = %(user)s",
                sysname=sysname, user=userid)
            db.execute(
                "UPDATE profile SET username = %(username)s WHERE userid = %(user)s",
                username=username, user=userid)
        d._get_display_name.invalidate(userid)
        updates.append('- Username: %s' % (username,))

    # Full name
    if full_name is not None:
        d.engine.execute(
            "UPDATE profile SET full_name = %(full_name)s WHERE userid = %(user)s",
            full_name=full_name, user=userid)
        updates.append('- Full name: %s' % (full_name,))

    # Catchphrase
    if catchphrase is not None:
        d.engine.execute(
            "UPDATE profile SET catchphrase = %(catchphrase)s WHERE userid = %(user)s",
            catchphrase=catchphrase, user=userid)
        updates.append('- Catchphrase: %s' % (catchphrase,))

    # Birthday
    if birthday is not None and d.convert_inputdate(birthday):
        unixtime = d.convert_inputdate(birthday)
        age = d.convert_age(unixtime)

        d.execute("UPDATE userinfo SET birthday = %i WHERE userid = %i", [unixtime, userid])

        if age < ratings.EXPLICIT.minimum_age:
            max_rating = ratings.GENERAL.code
            rating_flag = ""
        else:
            max_rating = ratings.EXPLICIT.code

        if d.get_rating(userid) > max_rating:
            d.engine.execute(
                """
                UPDATE profile
                SET config = REGEXP_REPLACE(config, '[ap]', '', 'g') || %(rating_flag)s
                WHERE userid = %(user)s
                """,
                rating_flag=rating_flag,
                user=userid,
            )
            d._get_all_config.invalidate(userid)
        updates.append('- Birthday: %s' % (birthday,))

    # Gender
    if gender is not None:
        d.engine.execute(
            "UPDATE userinfo SET gender = %(gender)s WHERE userid = %(user)s",
            gender=gender, user=userid)
        updates.append('- Gender: %s' % (gender,))

    # Location
    if country is not None:
        d.engine.execute(
            "UPDATE userinfo SET country = %(country)s WHERE userid = %(user)s",
            country=country, user=userid)
        updates.append('- Country: %s' % (country,))

    # Social and contact links
    if remove_social:
        for social_link in remove_social:
            d.engine.execute("DELETE FROM user_links WHERE userid = %(userid)s AND link_type = %(link)s", userid=userid, link=social_link)
            updates.append('- Removed social link for %s' % (social_link,))

    # Permissions
    if permission_tag is not None:
        if permission_tag:
            query = (
                "UPDATE profile SET config = replace(config, 'g', '') "
                "WHERE userid = %(user)s AND position('g' in config) != 0")
        else:
            query = (
                "UPDATE profile SET config = config || 'g' "
                "WHERE userid = %(user)s AND position('g' in config) = 0")

        if d.engine.execute(query, user=userid).rowcount != 0:
            updates.append('- Permission to tag: ' + ('yes' if permission_tag else 'no'))
            d._get_all_config.invalidate(userid)

    if updates:
        from weasyl import moderation
        moderation.note_about(my_userid, userid, 'The following fields were changed:', '\n'.join(updates))


def force_resetbirthday(userid, birthday):
    if not birthday:
        raise WeasylError("birthdayInvalid")
    elif birthday > d.get_time():
        raise WeasylError("birthdayInvalid")

    d.execute("UPDATE userinfo SET birthday = %i WHERE userid = %i", [birthday, userid])
    d.execute("UPDATE login SET settings = REPLACE(settings, 'i', '') WHERE userid = %i", [userid])
    d._get_all_config.invalidate(userid)


# TODO(hyena): Make this class unnecessary and remove it when we fix up settings.
class ProfileSettings(object):
    """
    This class standardizes access to jsonb profile settings,
    to ensure consistent use of naming conventions
    and defaults. This class will intentionally throw
    exceptions if you try to access a setting that has
    not been properly defined!
    """
    class Setting:
        def __init__(self, default, typecast):
            self.default = default
            self.typecast = typecast

    def _valid_rating(rating):
        rating = int(rating)
        return rating if rating in ratings.CODE_MAP else ratings.GENERAL.code

    _raw_settings = {}
    _settings = {
        "allow_collection_requests": Setting(True, bool),
        "allow_collection_notifs": Setting(True, bool),
        "disable_custom_thumbs": Setting(False, bool),
        "max_sfw_rating": Setting(ratings.GENERAL.code, _valid_rating),
    }

    def __init__(self, json):
        self._raw_settings = json

    def __getattr__(self, name):
        setting_config = self._settings[name]
        return self._raw_settings.get(name, setting_config.default)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super(ProfileSettings, self).__setattr__(name, value)
        else:
            setting_config = self._settings[name]
            if setting_config.typecast is not None:
                value = setting_config.typecast(value)
            self._raw_settings[name] = value

    def get_raw(self):
        return self._raw_settings


def sort_user_links(links):
    """Sorts the user's social/contact links.

    Args:
        links (list): User's links.

    Returns:
        Sorted list of links.
    """
    return sorted(map(tuple, links), key=lambda kv: kv[0].lower())

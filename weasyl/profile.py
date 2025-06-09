import datetime
import re

import arrow
import sqlalchemy as sa
from arrow import Arrow
from pyramid.threadlocal import get_current_request
from sqlalchemy import bindparam, func
from sqlalchemy.dialects.postgresql import aggregate_order_by

from libweasyl import ratings
from libweasyl import security
from libweasyl import staff
from libweasyl.cache import region
from libweasyl.legacy import UNIXTIME_NOW_SQL
from libweasyl.models import tables as t

from weasyl import define as d
from weasyl import emailer
from weasyl import login
from weasyl import macro as m
from weasyl import media
from weasyl import shout
from weasyl import welcome
from weasyl.configuration_builder import create_configuration, BoolOption, ConfigOption
from weasyl.error import WeasylError


class ExchangeType:
    __slots__ = ()


EXCHANGE_TYPE_TRADE = ExchangeType()
EXCHANGE_TYPE_REQUEST = ExchangeType()
EXCHANGE_TYPE_COMMISSION = ExchangeType()


class ExchangeSetting:
    __slots__ = ("code",)

    def __init__(self, code):
        self.code = code


EXCHANGE_SETTING_ACCEPTING = ExchangeSetting("o")
EXCHANGE_SETTING_SOMETIMES = ExchangeSetting("s")
EXCHANGE_SETTING_FULL_QUEUE = ExchangeSetting("f")
EXCHANGE_SETTING_NOT_ACCEPTING = ExchangeSetting("c")
EXCHANGE_SETTING_NOT_APPLICABLE = ExchangeSetting("e")

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
    ConfigOption("rating", dict(zip(ratings.ALL_RATINGS, ["", "a", "p"]))),
    BoolOption("tagging", "k"),
    BoolOption("hideprofile", "h"),
    BoolOption("hidestats", "i"),
    BoolOption("hidefavorites", "v"),
    BoolOption("hidefavbar", "u"),
    ConfigOption("shouts", {"anyone": "", "friends_only": "x", "staff_only": "w"}),
    ConfigOption("notes", {"anyone": "", "friends_only": "z", "staff_only": "y"}),
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


def resolve(userid, otherid, othername):
    """
    Attempts to determine the userid of a specified user; resolves using otherid,
    othername, and userid, in that order. If no userid can be
    resolved, returns 0 instead.
    """
    result = None

    if otherid:
        result = d.engine.scalar("SELECT userid FROM login WHERE userid = %(id)s", id=d.get_int(otherid))

        if result:
            return result
    elif othername:
        return resolve_by_username(othername)
    elif userid:
        return userid

    return 0


def resolve_by_username(username):
    return d.get_userids([username])[username]


_TWITTER_USERNAME = re.compile(r"@?(\w{4,15})", re.ASCII)

_TWITTER_USER_LINK = re.compile(
    r"(?:https?://)(?:(?:www|m|mobile)\.)?twitter.com/@?(\w{4,15})(?:\Z|[?#/])",
    re.ASCII | re.IGNORECASE
)


def _parse_twitter_username(twitter_link_value):
    """
    Get a Twitter username from a user-provided link if possible, or `None` if not.

    Preserves case.
    """
    twitter_link_value = twitter_link_value.strip()

    if m := _TWITTER_USERNAME.fullmatch(twitter_link_value):
        twitter_username = m.group(1)
    elif m := _TWITTER_USER_LINK.match(twitter_link_value):
        twitter_username = m.group(1)
    else:
        return None

    return twitter_username if twitter_username.lower() != "twitter" else None


_TWITTER_LINK_QUERY = (
    sa.select(t.user_links.c.link_value)
    .where(t.user_links.c.userid == bindparam("userid"))
    .where(t.user_links.c.link_type.ilike(sa.text("'twitter'")))
    .order_by(t.user_links.c.link_value)
    .limit(1)
).compile()


@region.cache_on_arguments()
def get_twitter_username(userid):
    link_value = d.engine.scalar(_TWITTER_LINK_QUERY, {"userid": userid})
    return _parse_twitter_username(link_value) if link_value else None


def select_profile(userid, viewer=None):
    query = d.engine.execute("""
        SELECT pr.username, pr.full_name, pr.catchphrase, pr.created_at, pr.profile_text,
            pr.settings, pr.stream_url, pr.config, pr.stream_text, us.end_time
        FROM profile pr
            LEFT JOIN user_streams us USING (userid)
        WHERE userid = %(user)s
    """, user=userid).first()

    if not query:
        raise WeasylError('userRecordMissing')

    is_banned, is_suspended = d.get_login_settings(userid)

    streaming_status = "stopped"
    if query[6]:  # profile.stream_url
        if 'l' in query[5]:
            streaming_status = "later"
        elif query[9] is not None and query[9] > d.get_time():  # user_streams.end_time
            streaming_status = "started"

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
        "banned": is_banned,
        "suspended": is_suspended,
        "streaming_status": streaming_status,
    }


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
    birthday = d.engine.scalar("SELECT birthday FROM userinfo WHERE userid = %(user)s", user=userid)
    return None if birthday is None else d.convert_age(birthday)


def get_user_ratings(userid):
    return ratings.get_ratings_for_age(get_user_age(userid))


def check_user_rating_allowed(userid, rating):
    # TODO(kailys): ensure usages always pass a Rating
    minimum_age = rating.minimum_age if isinstance(rating, ratings.Rating) else ratings.CODE_MAP[rating].minimum_age
    user_age = get_user_age(userid)
    if user_age is not None and user_age < minimum_age:
        raise WeasylError("ratingInvalid")


def select_userinfo(userid, config):
    query = d.engine.execute("""
        SELECT birthday, gender, country
        FROM userinfo
        WHERE userid = %(userid)s
    """, userid=userid).first()

    user_links = d.engine.execute("""
        SELECT link_type, ARRAY_AGG(link_value ORDER BY link_value)
        FROM user_links
        WHERE userid = %(userid)s
        GROUP BY link_type
    """, userid=userid).fetchall()

    show_age = "b" in config or d.get_userid() in staff.MODS
    return {
        "birthday": query.birthday,
        "age": d.convert_age(query.birthday) if show_age and query.birthday is not None else None,
        "show_age": "b" in config,
        "gender": query.gender,
        "country": query.country,
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
            (
                (SELECT coalesce(sum(favorites), 0) FROM submission WHERE userid = %(user)s) +
                (SELECT COUNT(*) FROM favorite fa JOIN character ch ON fa.targetid = ch.charid
                    WHERE ch.userid = %(user)s AND fa.type = 'f') +
                (SELECT COUNT(*) FROM favorite fa JOIN journal jo ON fa.targetid = jo.journalid
                    WHERE jo.userid = %(user)s AND fa.type = 'j')),
            (SELECT COUNT(*) FROM watchuser WHERE otherid = %(user)s),
            (SELECT COUNT(*) FROM watchuser WHERE userid = %(user)s),
            (SELECT COUNT(*) FROM submission WHERE userid = %(user)s AND NOT hidden),
            (SELECT COUNT(*) FROM journal WHERE userid = %(user)s AND NOT hidden),
            (SELECT COUNT(*) FROM comments WHERE target_user = %(user)s AND settings !~ 'h' AND settings ~ 's')
    """, user=userid).first()

    return {
        "page_views": query[0],
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


_SELECT_STREAMING_BASE = (
    sa.select(
        t.profile.c.userid,
        t.profile.c.username,
        t.profile.c.stream_url,
        t.profile.c.stream_text,
        t.user_streams.c.start_time.label('stream_time'),
    )
    .select_from(
        t.profile
        .join(t.user_streams, t.profile.c.userid == t.user_streams.c.userid)
        .join(t.login, t.profile.c.userid == t.login.c.userid),
    )
    .where(t.login.c.voucher.is_not(None))
    .where(t.user_streams.c.end_time > UNIXTIME_NOW_SQL)
    .where(t.profile.c.stream_url != sa.text("''"))
)


def select_streaming_sample(userid):
    query = _SELECT_STREAMING_BASE

    if userid:
        query = query.where(
            m.not_ignored(t.profile.c.userid)
            .unique_params({'userid': userid})
        )

    sample_subquery = (
        query
        .order_by(func.random())
        .limit(3)
        .subquery()
    )

    sample_and_count = sa.select(
        func.coalesce(
            sa.select(
                func.jsonb_agg(
                    aggregate_order_by(
                        sample_subquery.table_valued(),
                        sample_subquery.c.stream_time.desc(),
                    )
                ),
            )
            .select_from(sample_subquery)
            .scalar_subquery(),
            sa.text("'[]'::jsonb"),
        ).label('sample'),
        (sa.select(func.count())
            .select_from(query.subquery())
            .scalar_subquery()
            .label('total')),
    )

    ret = d.engine.execute(sample_and_count).one()
    media.populate_with_user_media(ret.sample)
    return ret


def select_streaming(userid):
    query = (
        _SELECT_STREAMING_BASE
        .order_by(t.user_streams.c.start_time.desc())
    )

    if userid:
        query = query.where(
            m.not_ignored(t.profile.c.userid)
            .unique_params({'userid': userid})
        )

    ret = [row._asdict() for row in d.engine.execute(query)]
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


def edit_streaming_settings(
    my_userid: int,
    userid: int,
    *,
    stream_text: str,
    stream_url: str,
    set_stream: str,
    stream_length: int = 0,
) -> None:

    stream_url = stream_url.strip()

    if stream_url:
        stream_url_parsed = d.text_fix_url(stream_url)
        if stream_url_parsed is None:
            raise WeasylError("streamLocationInvalid")
    else:
        stream_url_parsed = None

    if set_stream == 'start':
        if stream_length < 1 or stream_length > 360:
            raise WeasylError("streamDurationOutOfRange")

        if stream_url_parsed is None:
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
    result = d.engine.execute(
        pr.update()
        .where(pr.c.userid == userid)
        .values({
            'stream_text': stream_text,
            'stream_url': "" if stream_url_parsed is None else stream_url_parsed.href,
            'settings': sa.func.regexp_replace(pr.c.settings, "[nli]", "").concat(settings_flag),
        })
    )

    if result.rowcount != 1:
        raise WeasylError("Unexpected")

    if my_userid != userid:
        from weasyl import moderation
        note_body = (
            '- Stream url: %s\n'
            '- Stream description: %s\n'
            '- Stream status: %s' % (stream_url, stream_text, STREAMING_ACTION_MAP[set_stream]))
        moderation.note_about(my_userid, userid, 'Streaming settings updated:', note_body)


_MOST_ADVANCED_TIME_ZONE = datetime.timezone(datetime.timedelta(hours=14))

_BIRTHDATE_UPDATE_BASE = (
    t.userinfo.update()
    .where(t.userinfo.c.userid == bindparam("update_userid"))
    .where(t.userinfo.c.birthday.is_(None))
    .values(birthday=bindparam("birthday"))
)

_ASSERTED_ADULT = (
    sa.select(t.userinfo.c.asserted_adult)
    .where(t.userinfo.c.userid == bindparam("userid"))
)


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

    if form.show_age and form.get('birthdate-month') and form.get('birthdate-year'):
        birthdate_month = int(form['birthdate-month'])
        birthdate_year = int(form['birthdate-year'])

        if not (1 <= birthdate_month <= 12) or not (-125 <= birthdate_year - arrow.utcnow().year <= 0):
            raise WeasylError("birthdayInvalid")

        birthdate_update = _BIRTHDATE_UPDATE_BASE

        # If it is impossible* for someone born in the specified month to be 18+ and the user has asserted that they're 18+, don't allow it.
        # This is mainly to avoid inconsistency between the user's *displayed* age and their interactions.
        # (* I haven't explicitly accounted for all the weird time things that have happened in the world, but we can at least do time zones.)
        earliest_possible_utc_birthdate = (
            datetime.datetime(
                year=birthdate_year,
                month=birthdate_month,
                day=1,
                tzinfo=_MOST_ADVANCED_TIME_ZONE,
            )
            .astimezone(datetime.timezone.utc)
            .date()
        )
        oldest_possible_age = d.age_in_years(earliest_possible_utc_birthdate)
        if oldest_possible_age < 13:
            raise WeasylError("birthdayInconsistentWithTerms")

        is_age_restricted = oldest_possible_age < 18
        if is_age_restricted:
            birthdate_update = birthdate_update.where(~t.userinfo.c.asserted_adult)

        result = d.engine.execute(birthdate_update, {
            "update_userid": userid,
            "birthday": Arrow(year=birthdate_year, month=birthdate_month, day=1),
        })

        if result.rowcount != 1:
            assert result.rowcount == 0
            if is_age_restricted and d.engine.scalar(_ASSERTED_ADULT, {"userid": userid}):
                raise WeasylError("birthdayInconsistentWithRating")

            # otherwise, assume nothing was updated because a birthdate was already set

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
    get_twitter_username.invalidate(userid)


def edit_email_password(*, userid, password, newemail, newpassword):
    """
    Edit the email address and/or password for a given Weasyl account.

    After verifying the user's current login credentials, edit the user's email address and/or
    password if validity checks pass. If the email is modified, a confirmation email is sent
    to the user's target email with a token which, if used, finalizes the email address change.

    Parameters:
        userid: The `userid` of the Weasyl account to modify.
        password: The user's current plaintext password.
        newemail: If changing the email on the account, the new email address. Optional.
        newpassword: If changing the password, the user's new password. Optional.
    """
    from weasyl import login

    # Check that credentials are correct
    current_email = login.authenticate_account_change(
        userid=userid,
        password=password,
    )

    # Track if any changes were made for later display back to the user.
    changes_made = ""

    if newpassword and not login.password_secure(newpassword):
        raise WeasylError("passwordInsecure")

    # If we are setting a new email, then write the email into a holding table pending confirmation
    #   that the email is valid.
    if newemail and newemail.lower() != current_email.lower():
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
    sess = get_current_request().weasyl_session
    d.engine.execute("""
        DELETE FROM sessions
        WHERE userid = %(userid)s
          AND sessionid != %(currentsession)s
    """, userid=userid, currentsession=sess.sessionid if sess is not None else "")


def edit_preferences(userid,
                     preferences=None, jsonb_settings=None):
    """
    Apply changes to stored preferences for a given user.
    :param userid: The userid to apply changes to
    :param preferences: (optional) old-style char preferences, overwrites all previous settings
    :param jsonb_settings: (optional) JSON preferences, overwrites all previous settings
    :return: None
    """
    config = d.get_config(userid)
    user_age = get_user_age(userid)

    if preferences is not None and user_age is not None and user_age < preferences.rating.minimum_age:
        preferences.rating = ratings.GENERAL

    updates = {}
    if preferences is not None:
        # update legacy preferences
        # clear out the option codes that are being replaced.
        for i in Config.all_option_codes:
            config = config.replace(i, "")
        config_str = config + preferences.to_code()
        updates['config'] = config_str
    if jsonb_settings is not None:
        # update jsonb preferences
        updates['jsonb_settings'] = jsonb_settings.get_raw()

    if preferences is not None and preferences.rating.minimum_age:
        assert_adult(userid)

    d.engine.execute(
        t.profile.update().where(t.profile.c.userid == userid),
        updates
    )
    d._get_all_config.invalidate(userid)


def assert_adult(userid):
    """
    Set a flag on a user indicating that they’ve asserted they’re 18 or older in performing some operation.
    """
    d.engine.execute(
        t.userinfo.update().where(t.userinfo.c.userid == userid),
        {
            'asserted_adult': True,
        },
    )


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
            pr.created_at, pr.username, pr.full_name, pr.catchphrase,
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
        "staff_notes": shout.count_staff_notes(userid),
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
        birthday (str): New birthday for user, in HTML5 date format (ISO 8601 yyyy-mm-dd). Defaults to None.
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
        login.change_username(
            acting_user=my_userid,
            target_user=userid,
            bypass_limit=True,
            new_username=username,
        )

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
    if birthday is not None:
        if birthday == "":
            unixtime = None
            age = None
        else:
            # HTML5 date format is yyyy-mm-dd
            split = birthday.split("-")
            if len(split) != 3 or d.convert_unixdate(day=split[2], month=split[1], year=split[0]) is None:
                raise WeasylError("birthdayInvalid")
            unixtime = d.convert_unixdate(day=split[2], month=split[1], year=split[0])
            age = d.convert_age(unixtime)

        result = d.engine.execute("UPDATE userinfo SET birthday = %(birthday)s WHERE userid = %(user)s", birthday=unixtime, user=userid)
        assert result.rowcount == 1

        if age is not None and age < ratings.EXPLICIT.minimum_age:
            # reset rating preference and SFW mode rating preference to General
            d.engine.execute(
                """
                UPDATE profile
                SET config = REGEXP_REPLACE(config, '[ap]', '', 'g')
                WHERE userid = %(user)s
                """,
                user=userid,
            )
            d._get_all_config.invalidate(userid)
        updates.append('- Birthday: %s' % (birthday or 'removal',))

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


# TODO(hyena): Make this class unnecessary and remove it when we fix up settings.
class ProfileSettings:
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

    _raw_settings = {}
    _settings = {
        "allow_collection_requests": Setting(True, bool),
        "allow_collection_notifs": Setting(True, bool),
        "disable_custom_thumbs": Setting(False, bool),
    }

    def __init__(self, json):
        self._raw_settings = json

    def __getattr__(self, name):
        setting_config = self._settings[name]
        return self._raw_settings.get(name, setting_config.default)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
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

# profile.py

from translationstring import TranslationString as _

from error import WeasylError
import macro as m
import define as d

import pytz

import orm
import shout
import welcome

from libweasyl.html import strip_html
from libweasyl.models import tables
from libweasyl import ratings
from libweasyl import staff

from weasyl.cache import region
from weasyl.configuration_builder import create_configuration, BoolOption, ConfigOption
from weasyl import media


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
    ConfigOption("rating", dict(zip(ratings.ALL_RATINGS, ["", "m", "a", "p"]))),
    BoolOption("tagging", "k"),
    BoolOption("edittagging", "r"),
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


def resolve(userid, otherid, othername, myself=True):
    """
    Attempts to determine the userid of a specified user; resolves using otherid,
    othername, and userid (if myself is True), in that order. If no userid can be
    resolved, returns 0 instead.
    """
    result = None

    if otherid:
        result = d.execute("SELECT userid FROM login WHERE userid = %i", [d.get_int(otherid)], ["element"])

        if result:
            return result
    elif othername:
        result = d.execute("SELECT userid FROM login WHERE login_name = '%s'", [d.get_sysname(othername)], ["element"])

        if result:
            return result

        result = d.execute("SELECT userid FROM useralias WHERE alias_name = '%s'", [d.get_sysname(othername)], ["element"])

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
    query = d.execute("""
        SELECT pr.username, pr.full_name, pr.catchphrase, pr.unixtime, pr.profile_text,
            pr.settings, pr.stream_url, pr.config, pr.stream_text, lo.settings, us.end_time
        FROM profile pr
            INNER JOIN login lo USING (userid)
            LEFT JOIN user_streams us USING (userid)
        WHERE userid = %i
    """, [userid], ["single"])

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
    username, full_name, catchphrase, profile_text, config, twitter = d.execute(
        "SELECT pr.username, pr.full_name, pr.catchphrase, pr.profile_text, pr.config, ul.link_value "
        "FROM profile pr "
        "LEFT JOIN user_links ul ON pr.userid = ul.userid AND ul.link_type = 'twitter' "
        "WHERE pr.userid = %i",
        [userid],
        ["single"])

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
        return

    query = d.execute("SELECT username, config FROM profile WHERE userid = %i", [userid], ["single"])

    return {
        "userid": userid,
        "username": query[0],
        "is_mod": userid in staff.MODS,
        "user_media": media.get_user_media(userid),
    }


def get_user_age(userid):
    assert userid
    return d.convert_age(d.execute("SELECT birthday FROM userinfo WHERE userid = %i", [userid], ["element"]))


def get_user_ratings(userid):
    return ratings.get_ratings_for_age(get_user_age(userid))


def check_user_rating_allowed(userid, rating):
    # TODO(kailys): ensure usages always pass a Rating
    minimum_age = rating.minimum_age if isinstance(rating, ratings.Rating) else ratings.CODE_MAP[rating].minimum_age
    if get_user_age(userid) < minimum_age:
        raise WeasylError("ratingInvalid")


def select_userinfo(userid, config=None):
    if config is None:
        [query] = d.engine.execute("""
            SELECT pr.config, ui.birthday, ui.gender, ui.country
            FROM profile pr
            INNER JOIN userinfo ui USING (userid)
            WHERE pr.userid = %(userid)s
        """, userid=userid)
    else:
        [query] = d.engine.execute("""
            SELECT %(config)s, birthday, gender, country
            FROM userinfo
            WHERE userid = %(userid)s
        """, userid=userid, config=config)

    user_link_rows = d.engine.execute("""
        SELECT link_type, ARRAY_AGG(link_value)
        FROM user_links
        WHERE userid = %(userid)s
        GROUP BY link_type
    """, userid=userid)
    user_links = {r[0]: r[1] for r in user_link_rows}

    show_age = "b" in query[0] or d.get_userid() in staff.MODS
    return {
        "birthday": query[1],
        "age": d.convert_age(query[1]) if show_age else None,
        "show_age": "b" in query[0],
        "gender": query[2],
        "country": query[3],
        "user_links": user_links,
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
            "is_self": userid == otherid,
        }

    query = d.engine.execute("""
        SELECT
            (SELECT EXISTS (SELECT 0 FROM watchuser WHERE (userid, otherid) = (%(user)s, %(other)s))),
            (SELECT EXISTS (SELECT 0 FROM frienduser WHERE userid IN (%(user)s, %(other)s) AND otherid IN (%(user)s, %(other)s) AND settings !~ 'p')),
            (SELECT EXISTS (SELECT 0 FROM ignoreuser WHERE (userid, otherid) = (%(user)s, %(other)s))),
            (SELECT EXISTS (SELECT 0 FROM frienduser WHERE (userid, otherid) = (%(user)s, %(other)s) AND settings ~ 'p')),
            (SELECT EXISTS (SELECT 0 FROM watchuser WHERE (userid, otherid) = (%(user)s, %(other)s)))
    """, user=userid, other=otherid).first()

    return {
        "follow": query[0],
        "friend": query[1],
        "ignore": query[2],
        "friendreq": query[3],
        "follower": query[4],
        "is_self": False,
    }


@region.cache_on_arguments(expiration_time=600)
@d.record_timing
def _select_statistics(userid):
    query = d.execute("""
        SELECT
            (SELECT page_views FROM profile WHERE userid = %i),
            0,
            (SELECT COUNT(*) FROM favorite WHERE userid = %i),
            (SELECT
                (SELECT COUNT(*) FROM favorite fa JOIN submission su ON fa.targetid = su.submitid
                    WHERE su.userid = %i AND fa.type = 's') +
                (SELECT COUNT(*) FROM favorite fa JOIN character ch ON fa.targetid = ch.charid
                    WHERE ch.userid = %i AND fa.type = 'f') +
                (SELECT COUNT(*) FROM favorite fa JOIN journal jo ON fa.targetid = jo.journalid
                    WHERE jo.userid = %i AND fa.type = 'j')),
            (SELECT COUNT(*) FROM watchuser WHERE otherid = %i),
            (SELECT COUNT(*) FROM watchuser WHERE userid = %i),
            (SELECT COUNT(*) FROM submission WHERE userid = %i AND settings !~ 'h'),
            (SELECT COUNT(*) FROM journal WHERE userid = %i AND settings !~ 'h'),
            (SELECT COUNT(*) FROM comments WHERE target_user = %i AND settings !~ 'h' AND settings ~ 's')
    """, [userid, userid, userid, userid, userid, userid, userid, userid, userid, userid], options="single")

    return {
        "page_views": query[0],
        "submit_views": query[1],
        "faves_sent": query[2],
        "faves_received": query[3],
        "followed": query[4],
        "following": query[5],
        "submissions": query[6],
        "journals": query[7],
        "staff_notes": query[8],
    }


def select_statistics(userid):
    if "i" in d.get_config(userid) and d.get_userid() not in staff.MODS:
        return
    return _select_statistics(userid)


def select_streaming(userid, rating, limit, following=True, order_by=None):
    statement = [
        "SELECT userid, pr.username, pr.stream_url, pr.config, pr.stream_text, start_time "
        "FROM profile pr "
        "JOIN user_streams USING (userid) "
        "WHERE end_time > %i" % (d.get_time(),)
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

    results = d.execute(
        "SELECT userid, username, config FROM profile pr WHERE userid IN %s" % (d.sql_number_list(userids),))
    results = [
        {
            "username": username,
            "userid": userid,
        }
        for userid, username, config in results]
    media.populate_with_user_media(results)
    return {d['userid']: d for d in results}


def edit_profile(userid, profile,
                 set_trade=EXCHANGE_SETTING_NOT_ACCEPTING,
                 set_request=EXCHANGE_SETTING_NOT_ACCEPTING,
                 set_commission=EXCHANGE_SETTING_NOT_ACCEPTING,
                 profile_display=''):
    # Assign settings
    settings = "".join([set_commission.code, set_trade.code, set_request.code])

    if profile_display not in ('O', 'A'):
        profile_display = ''

    d.execute(
        "UPDATE profile "
        "SET (full_name, catchphrase, profile_text, settings) = ('%s', '%s', '%s', '%s'), "
        "config = REGEXP_REPLACE(config, '[OA]', '') || '%s'"
        "WHERE userid = %i",
        [profile.full_name, profile.catchphrase, profile.profile_text, settings, profile_display, userid])
    d._get_config.invalidate(userid)


STREAMING_ACTION_MAP = {
    '': 'not streaming',
    'later': 'streaming later',
    'start': 'now streaming',
    'still': 'still streaming',
}


def edit_streaming_settings(my_userid, userid, profile, set_stream=None, stream_length=0):

    if set_stream == 'start':
        try:
            stream_length = int(stream_length)
        except:
            raise WeasylError("streamDurationOutOfRange")

        if stream_length < 1 or stream_length > 360:
            raise WeasylError("streamDurationOutOfRange")

    if set_stream == 'start' and not profile.stream_url:
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

    d.execute(
        "UPDATE profile "
        "SET (stream_text, stream_url, settings) = ('%s', '%s', REGEXP_REPLACE(settings, '[nli]', '') || '%s') "
        "WHERE userid = %i",
        [profile.stream_text, profile.stream_url, settings_flag, userid])

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
        row['userid'] = userid
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

    d._get_config.invalidate(userid)


def edit_email_password(userid, username, password, newemail, newemailcheck,
                        newpassword, newpasscheck):
    import login

    # Check that credentials are correct
    logid, logerror = login.authenticate_bcrypt(username, password, session=False)

    if userid != logid or logerror is not None:
        raise WeasylError("loginInvalid")

    if newemail:
        if newemail != newemailcheck:
            raise WeasylError("emailMismatch")
        elif login.email_exists(newemail):
            raise WeasylError("emailExists")

    if newpassword:
        if newpassword != newpasscheck:
            raise WeasylError("passwordMismatch")
        elif not login.password_secure(newpassword):
            raise WeasylError("passwordInsecure")

    if newemail:
        d.execute("UPDATE login SET email = '%s' WHERE userid = %i", [newemail, userid])

    if newpassword:
        d.execute("UPDATE authbcrypt SET hashsum = '%s' WHERE userid = %i", [login.passhash(newpassword), userid])


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
        d._get_config.invalidate(userid)
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
    query = d.execute("""
        SELECT
            lo.userid, lo.last_login, lo.email, pr.unixtime, pr.username, pr.full_name, pr.catchphrase, ui.birthday,
            ui.gender, ui.country, pr.config
        FROM login lo
            INNER JOIN profile pr USING (userid)
            INNER JOIN userinfo ui USING (userid)
        WHERE lo.userid = %i
    """, [userid], ["single"])

    if not query:
        raise WeasylError("Unexpected")

    return {
        "userid": query[0],
        "last_login": query[1],
        "email": query[2],
        "unixtime": query[3],
        "username": query[4],
        "full_name": query[5],
        "catchphrase": query[6],
        "birthday": query[7],
        "gender": query[8],
        "country": query[9],
        "config": query[10],
        "staff_notes": shout.count(userid, staffnotes=True),
    }


def do_manage(my_userid, userid, username=None, full_name=None, catchphrase=None,
              birthday=None, gender=None, country=None):
    updates = []

    # Username
    if username is not None:
        if not d.get_sysname(username):
            raise WeasylError("usernameInvalid")
        elif d.execute("SELECT EXISTS (SELECT 0 FROM login WHERE login_name = '%s')",
                       [d.get_sysname(username)], ["bool"]):
            raise WeasylError("usernameExists")
        elif d.execute("SELECT EXISTS (SELECT 0 FROM useralias WHERE alias_name = '%s')",
                       [d.get_sysname(username)], ["bool"]):
            raise WeasylError("usernameExists")
        elif d.execute("SELECT EXISTS (SELECT 0 FROM logincreate WHERE login_name = '%s')",
                       [d.get_sysname(username)], ["bool"]):
            raise WeasylError("usernameExists")

        d.execute("UPDATE login SET login_name = '%s' WHERE userid = %i",
                  [d.get_sysname(username), userid])
        d._get_display_name.invalidate(userid)
        d.execute("UPDATE profile SET username = '%s' WHERE userid = %i",
                  [username, userid])
        updates.append('- Username: %s' % (username,))

    # Full name
    if full_name is not None:
        d.execute("UPDATE profile SET full_name = '%s' WHERE userid = %i",
                  [full_name, userid])
        updates.append('- Full name: %s' % (full_name,))

    # Catchphrase
    if catchphrase is not None:
        d.execute("UPDATE profile SET catchphrase = '%s' WHERE userid = %i",
                  [catchphrase, userid])
        updates.append('- Catchphrase: %s' % (catchphrase,))

    # Birthday
    if birthday is not None and d.convert_inputdate(birthday):
        unixtime = d.convert_inputdate(birthday)
        age = d.convert_age(unixtime)

        d.execute("UPDATE userinfo SET birthday = %i WHERE userid = %i", [unixtime, userid])

        if age < ratings.MODERATE.minimum_age:
            max_rating = ratings.GENERAL.code
            rating_flag = ""
        elif age < ratings.EXPLICIT.minimum_age:
            max_rating = ratings.MODERATE.code
            rating_flag = "m"
        else:
            max_rating = ratings.EXPLICIT.code

        if d.get_rating(userid) > max_rating:
            d.execute(
                """
                UPDATE profile
                SET config = REGEXP_REPLACE(config, '[map]', '', 'g') || '%s'
                WHERE userid = %i
                """,
                [rating_flag, userid]
            )
            d._get_config.invalidate(userid)
        updates.append('- Birthday: %s' % (birthday,))

    # Gender
    if gender is not None:
        d.execute("UPDATE userinfo SET gender = '%s' WHERE userid = %i",
                  [gender, userid])
        updates.append('- Gender: %s' % (gender,))

    # Location
    if country is not None:
        d.execute("UPDATE userinfo SET country = '%s' WHERE userid = %i",
                  [country, userid])
        updates.append('- Country: %s' % (country,))

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
    d.get_login_settings.invalidate(userid)


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

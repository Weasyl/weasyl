import re
from collections import namedtuple
from decimal import Decimal
from urllib.parse import quote as urlquote

from psycopg2.errorcodes import UNIQUE_VIOLATION
from sqlalchemy.exc import OperationalError

from libweasyl.cache import region

from weasyl import config
from weasyl import define as d
from weasyl import macro as m
from weasyl.error import WeasylError
from weasyl.users import Username

_MAX_PRICE = 99999999

CURRENCY_PRECISION = 2

Currency = namedtuple('Currency', ('code', 'name', 'symbol'))

# map database charset to ISO4217 currency codes
CURRENCY_CHARMAP = {
    "": Currency(code="USD", name="United States Dollar", symbol="$"),
    "e": Currency(code="EUR", name="Euro", symbol="€"),
    "p": Currency(code="GBP", name="British Pound Sterling", symbol="£"),
    "y": Currency(code="JPY", name="Japanese Yen", symbol="J¥"),
    "c": Currency(code="CAD", name="Canadian Dollar", symbol="C$"),
    "m": Currency(code="MXN", name="Mexican Peso", symbol="M$"),
    "u": Currency(code="AUD", name="Australian Dollar", symbol="A$"),
    "z": Currency(code="NZD", name="New Zealand Dollar", symbol="NZ$"),
    "n": Currency(code="CNY", name="Chinese Yuan", symbol="C¥"),
    "f": Currency(code="CHF", name="Swiss Franc", symbol="Fr"),
}

# These are to be used as a general guide for both artists and commissioners
# to standardize some commission types until a more robust system
# of searching for commissions is put in place
PRESET_COMMISSION_CLASSES = [
    ("Visual", ["Sketch", "Badge", "Icon", "Reference", "Fullbody", "Headshot", "Chibi"]),
    ("Literary", ["Story"]),
    ("Multimedia", ["Music"]),
]


def parse_currency(target):
    """
    Return the target string as a price integer; for example, "$1.23" becomes
    123 which can then be stored in the database.
    """
    if not target:
        return 0
    # strip everything but digits and a decimal point
    digits = re.sub("[^0-9.]", "", target)
    if not digits:
        return 0
    return int(Decimal(digits) * (10 ** CURRENCY_PRECISION))


@region.cache_on_arguments(expiration_time=60 * 60 * 24, should_cache_fn=bool)
def _fetch_rates_no_cache_failure():
    """
    Retrieve most recent currency exchange rates from the European Central Bank.

    This value is cached with a 24h expiry period. Failures are cached for one hour.
    """
    if not config.config_read_bool('convert_currency'):
        return None

    try:
        response = d.http_get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")
    except WeasylError:
        # http_get already logged the exception
        return None

    rates = {'EUR': 1.0}

    for match in re.finditer(r"currency='([A-Z]{3})' rate='([0-9.]+)'", response.text):
        code, rate = match.groups()

        try:
            rate = float(rate)
        except ValueError:
            pass
        else:
            if 0.0 < rate < float('inf'):
                rates[code] = rate

    return rates


@region.cache_on_arguments(expiration_time=60 * 60)
def _fetch_rates():
    return _fetch_rates_no_cache_failure()


def _charmap_to_currency_code(charmap):
    """
    Convert Weasyl's internal single-character representation of currencies
    to standard ISO4217 codes for use in comparing against exchange rate APIs

    :param charmap: String containing ideally one or zero characters used as currency indicators by Weasyl
    :return: A 3-letter ISO4217 currency code. Returns "USD" if no match found.
    """
    for c in charmap:
        if c in CURRENCY_CHARMAP:
            return CURRENCY_CHARMAP[c].code
    return "USD"


def convert_currency(value, valuecode, targetcode):
    """
    Convert between different currencies using the current exchange rate.

    :param value: The amount of currency to be converted
    :param valuecode: Weasyl-code of the currency $value is in currently
    :param targetcode: Weasyl-code of the currency $value should be converted to
    :return: The converted amount. If a conversion cannot be made, may return None.
    """
    if targetcode == valuecode:
        return value
    ratio = currency_ratio(valuecode, targetcode)
    if ratio:
        return value * ratio
    else:
        return None


def currency_ratio(valuecode, targetcode):
    """
    Calculate the exchange rate multiplier used to convert from $valuecode to $targetcode

    :param valuecode: Weasyl-code of the currency $value is in currently
    :param targetcode: Weasyl-code of the currency $value should be converted to
    :return: The conversion ratio. If a ratio cannot be found, may return None.
    """
    valuecode = _charmap_to_currency_code(valuecode)
    targetcode = _charmap_to_currency_code(targetcode)
    rates = _fetch_rates()

    if rates is None:
        return None

    r1 = rates.get(valuecode)
    r2 = rates.get(targetcode)

    if r1 is None or r2 is None:
        return None

    return r2 / r1


def select_list(userid):
    query = d.engine.execute("""
        SELECT classid, title, amount_min, amount_max, settings, priceid FROM commishprice
        WHERE userid = %(userid)s ORDER BY classid, title
    """, userid=userid)

    classes = d.engine.execute("""
        SELECT classid, title FROM commishclass
        WHERE userid = %(id)s ORDER BY title
    """, id=userid)

    content = d.engine.scalar("""
        SELECT content FROM commishdesc
        WHERE userid = %(id)s
    """, id=userid)

    preference_tags = d.engine.execute("""
        SELECT DISTINCT tag.title FROM searchtag tag
        JOIN artist_preferred_tags pref ON pref.tagid = tag.tagid
        WHERE pref.targetid = %(userid)s
    """, userid=userid).fetchall()

    optout_tags = d.engine.execute("""
        SELECT DISTINCT tag.title FROM searchtag tag
        JOIN artist_optout_tags pref ON pref.tagid = tag.tagid
        WHERE pref.targetid = %(userid)s
    """, userid=userid).fetchall()

    return {
        "userid": userid,
        "class": [{
            "classid": i.classid,
            "title": i.title,
        } for i in classes],
        "price": [{
            "classid": i.classid,
            "title": i.title,
            "amount_min": i.amount_min,
            "amount_max": i.amount_max,
            "settings": i.settings,
            "priceid": i.priceid,
        } for i in query],
        "content": content if content else "",
        "tags": [tag.title for tag in preference_tags],
        "opt_out": [tag.title for tag in optout_tags],
    }


def select_commissionable(userid, q, commishclass, min_price, max_price, currency, offset, limit):
    """
    Select a list of artists who are open for commissions
    and have defined at least one commission class.

    This query sorts primarily by how many matching tags in the "content" field match
    an artist's preferred tags. Secondarily, it sorts by the artist's most recent upload time
    (of any submission that is not hidden or friends-only).
    This way artists who are more active on the site will receive a higher search ranking.
    Ignored artists and banned/suspended artists will not appear in search results.

    Commission prices are converted to $currency before being compared against min_price and max_price.
    This way, a search with a min price of "1000 JPY" can still return a result for a commission
    class with a price of 20 USD.

    If possible, the query will return the number of relevant examples (submissions matching a tag from $q
    or the name of the commission class) in each user's gallery and a link to a search to view them.

    TODO:
        - relax the requirement for setting up commission classes
        - redo the entire thing when (if) commissioninfo has (gets) a better schema

    :param userid: The user making the request
    :param q: "Content" query / tags, weight artists with "preferred content" tags that match these higher
    :param commishclass: Only return artists with at least one commission class containing this keyword
    :param min_price: Do not return artists with a minimum price below this value
    :param max_price: Do not return artists with a minimum price above this value
    :param currency: The single-character currency code to convert the returned results in,
                     as defined in commishprice.settings
    :param offset: Results set offset for pagination. Must be a positive Number
    :param limit: max number of results to return
    :return: The resulting list of artists & their commission info
    """
    stmt = ["""
        SELECT p.userid, p.username, p.settings,
            MIN(cp.amount_min) AS pricemin,
            GREATEST(MAX(cp.amount_max), MAX(cp.amount_min)) AS pricemax,
            MIN(cp.settings) AS pricesettings,
            MAX(d.content) AS description,
            COUNT(preftag.tagid) AS tagcount,
            STRING_AGG(DISTINCT cc.title, ', ') AS class
        FROM commishclass cc

        JOIN profile p ON cc.userid = p.userid

        JOIN login ON p.userid = login.userid

        JOIN commishprice cp ON cp.classid = cc.classid
            AND cp.userid = p.userid
            AND cp.settings NOT LIKE '%%a'

        LEFT JOIN commishdesc d ON p.userid = d.userid

        LEFT JOIN artist_preferred_tags prefmap ON p.userid = prefmap.targetid

        LEFT JOIN searchtag preftag ON prefmap.tagid = preftag.tagid
            AND preftag.title = ANY(%(tags)s)

        WHERE LOWER(cc.title) LIKE %(cclasslike)s
        AND p.settings ~ '^[os]'
        AND NOT EXISTS (SELECT FROM permaban WHERE permaban.userid = login.userid)
        AND NOT EXISTS (SELECT FROM suspension WHERE suspension.userid = login.userid)
        AND login.voucher IS NOT NULL
        AND NOT EXISTS (
            SELECT 0
            FROM searchtag tag
            JOIN artist_optout_tags map ON map.tagid = tag.tagid
            WHERE tag.title = ANY(%(tags)s)
            AND map.targetid = p.userid
        )
    """]
    if min_price:
        for c in CURRENCY_CHARMAP:
            local_min = convert_currency(min_price, currency, c)
            if local_min:
                stmt.append("AND NOT (cp.settings ~ '^%s' AND cp.amount_min < %f)\n" % (c, local_min))
    if max_price:
        for c in CURRENCY_CHARMAP:
            local_max = convert_currency(max_price, currency, c)
            if local_max:
                stmt.append("AND NOT (cp.settings ~ '^%s' AND cp.amount_min > %f)\n" % (c, local_max))
    tags = q.lower().split()
    if userid:
        stmt.append(m.MACRO_IGNOREUSER % (userid, "p"))
    stmt.append("""
        GROUP BY p.userid
        ORDER BY
    """)
    if commishclass:
        # If we are searching for a specific commission class, put closest matches
        # near the top of the list. This is necessary because we allow partial matches
        # on class names eg badge -> badges.
        # however, we want the other orderings to really have more importance overall,
        # so it's lumped into two categories of "close" (<=2) and "not close" (>2)
        stmt.append("""
            LEAST(GREATEST(MIN(LEVENSHTEIN(LOWER(cc.title), %(cclass)s)), 2), 3),
        """)
        # As well, use searched class as a tag for purposes of finding "tagged" examples of an artists work
        tags.append(commishclass)
    stmt.append("""
            COALESCE(COUNT(preftag.tagid), 0) DESC, p.latest_submission_time DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """)
    # to allow partial matches on commishclass
    cclasslike = "%" + commishclass + "%"
    max_rating = d.get_rating(userid)
    query = d.engine.execute("".join(stmt), limit=limit, min=min_price,
                             max=max_price, cclass=commishclass, cclasslike=cclasslike,
                             tags=tags, rating=max_rating, offset=offset)

    def prepare(info):
        dinfo = dict(info)
        dinfo['localmin'] = convert_currency(info.pricemin, info.pricesettings, currency)
        dinfo['localmax'] = convert_currency(info.pricemax, info.pricesettings, currency)
        if tags:
            terms = ["user:" + Username.from_stored(info.username).sysname] + ["|" + tag for tag in tags]
            dinfo['searchquery'] = "q=" + urlquote(" ".join(terms).encode("utf-8"))
        else:
            dinfo['searchquery'] = ""
        return dinfo

    results = [prepare(i) for i in query]
    return results


def create_commission_class(userid, title):
    """
    Creates a new commission class and returns its id.
    """
    if not title:
        raise WeasylError("titleInvalid")

    classid = d.engine.scalar("SELECT MAX(classid) + 1 FROM commishclass WHERE userid = %(user)s", user=userid)
    if not classid:
        classid = 1
    try:
        d.engine.execute(
            "INSERT INTO commishclass VALUES (%(class_)s, %(user)s, %(title)s)",
            class_=classid,
            user=userid,
            title=title,
        )
        return classid
    except OperationalError as e:
        if e.orig.pgcode != UNIQUE_VIOLATION:
            raise
        raise WeasylError("commishclassExists")


def create_price(userid, price, currency="", settings=""):
    if not price.title:
        raise WeasylError("titleInvalid")
    elif price.amount_min > _MAX_PRICE:
        raise WeasylError("minamountInvalid")
    elif price.amount_max > _MAX_PRICE:
        raise WeasylError("maxamountInvalid")
    elif price.amount_max and price.amount_max < price.amount_min:
        raise WeasylError("maxamountInvalid")
    elif not price.classid:
        raise WeasylError("classidInvalid")
    elif not d.engine.scalar("SELECT EXISTS (SELECT 0 FROM commishclass WHERE (classid, userid) = (%(class_)s, %(user)s))",
                             class_=price.classid, user=userid):
        raise WeasylError("classidInvalid")

    # Settings are at most one currency class, and optionally an 'a' to indicate an add-on price.
    # TODO: replace these character codes with an enum.
    settings = "%s%s" % ("".join(i for i in currency if i in CURRENCY_CHARMAP)[:1],
                         "a" if "a" in settings else "")

    # TODO: should have an auto-increment ID
    priceid = d.engine.scalar("SELECT MAX(priceid) + 1 FROM commishprice WHERE userid = %(user)s", user=userid)

    try:
        d.engine.execute(
            "INSERT INTO commishprice VALUES (%(newid)s, %(class_)s, %(user)s, %(title)s, %(amount_min)s, %(amount_max)s, %(settings)s)",
            newid=priceid if priceid else 1,
            class_=price.classid,
            user=userid,
            title=price.title,
            amount_min=price.amount_min,
            amount_max=price.amount_max,
            settings=settings,
        )
    except OperationalError as e:
        if e.orig.pgcode != UNIQUE_VIOLATION:
            raise
        raise WeasylError("titleExists")


def edit_class(userid, commishclass):
    if not commishclass.title:
        raise WeasylError("titleInvalid")

    try:
        d.engine.execute(
            "UPDATE commishclass SET title = %(title)s WHERE (classid, userid) = (%(class_)s, %(user)s)",
            title=commishclass.title,
            class_=commishclass.classid,
            user=userid,
        )
    except OperationalError as e:
        if e.orig.pgcode != UNIQUE_VIOLATION:
            raise
        raise WeasylError("titleExists")


def edit_price(userid, price, currency, settings, edit_prices):
    if price.amount_min > _MAX_PRICE:
        raise WeasylError("minamountInvalid")
    elif price.amount_max > _MAX_PRICE:
        raise WeasylError("maxamountInvalid")
    elif price.amount_max and price.amount_max < price.amount_min:
        raise WeasylError("maxamountInvalid")

    currency = "".join(i for i in currency if i in CURRENCY_CHARMAP)
    settings = "".join(i for i in settings if i in "a")

    updates = {
        'settings': currency + settings,
    }

    if price.title:
        updates['title'] = price.title

    if edit_prices:
        updates['amount_min'] = price.amount_min
        updates['amount_max'] = price.amount_max

    cpt = d.meta.tables['commishprice']
    result = d.engine.execute(
        cpt.update()
        .where(cpt.c.priceid == price.priceid)
        .where(cpt.c.userid == userid)
        .values(updates)
    )

    if result.rowcount != 1:
        raise WeasylError("priceidInvalid")


def edit_content(userid, content):
    d.engine.execute(
        "INSERT INTO commishdesc (userid, content)"
        " VALUES (%(user)s, %(content)s)"
        " ON CONFLICT (userid) DO UPDATE SET content = %(content)s",
        user=userid,
        content=content,
    )


def remove_class(userid, classid):
    with d.engine.begin() as db:
        result = db.execute(
            "DELETE FROM commishclass WHERE (classid, userid) = (%(class_)s, %(user)s)",
            class_=classid,
            user=userid,
        )

        if result.rowcount != 1:
            raise WeasylError("classidInvalid")

        db.execute(
            "DELETE FROM commishprice WHERE (classid, userid) = (%(class_)s, %(user)s)",
            class_=classid,
            user=userid,
        )


def remove_price(userid, priceid):
    result = d.engine.execute(
        "DELETE FROM commishprice WHERE (priceid, userid) = (%(price)s, %(user)s)",
        price=priceid,
        user=userid,
    )

    if result.rowcount != 1:
        raise WeasylError("priceidInvalid")

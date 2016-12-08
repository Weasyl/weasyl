from __future__ import absolute_import

from weasyl import macro as m
from weasyl.cache import region
from weasyl.error import WeasylError
import re
import urllib
from decimal import Decimal

from weasyl import define as d
from weasyl import error

_MAX_PRICE = 99999999

CURRENCY_PRECISION = 2

# map database charset to ISO4217 currency codes
CURRENCY_CHARMAP = {
    "": {"code": "USD", "name": "United States Dollar", "symbol": "&#36;"},
    "e": {"code": "EUR", "name": "Euro", "symbol": "&#8364;"},
    "p": {"code": "GBP", "name": "British Pound Sterling", "symbol": "&#163;"},
    "y": {"code": "JPY", "name": "Japanese Yen", "symbol": "J&#165;"},
    "c": {"code": "CAD", "name": "Canadian Dollar", "symbol": "C&#36;"},
    "m": {"code": "MXN", "name": "Mexican Peso", "symbol": "M&#36;"},
    "u": {"code": "AUD", "name": "Australian Dollar", "symbol": "A&#36;"},
    "z": {"code": "NZD", "name": "New Zealand Dollar", "symbol": "NZ&#36;"},
    "n": {"code": "CNY", "name": "Chinese Yuan", "symbol": "C&#165;"},
    "f": {"code": "CHF", "name": "Swiss Franc", "symbol": "Fr"},
}

# These are to be used as a general guide for both artists and commissioners
# to standardize some commission types until a more robust system
# of searching for commissions is put in place
PRESET_COMMISSION_CLASSES = [
    "Sketch",
    "Badge",
    "Icon",
    "Reference",
    "Story",
    "Music",
    "Fullbody",
    "Headshot",
    "Chibi",
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


@region.cache_on_arguments(expiration_time=60 * 60 * 24)
def _fetch_rates():
    """
    Retrieves most recent currency exchange rates from fixer.io, which uses
    the European Central Bank as its upstream source.

    This value is cached with a 24h expiry period

    :return: see http://fixer.io/
    """
    try:
        return d.http_get("http://api.fixer.io/latest?base=USD").json()
    except WeasylError:
        # There was an HTTP error while fetching from the API
        return None


def _charmap_to_currency_code(charmap):
    """
    Convert Weasyl's internal single-character representation of currencies
    to standard ISO4217 codes for use in comparing against exchange rate APIs

    :param charmap: String containing ideally one or zero characters used as currency indicators by Weasyl
    :return: A 3-letter ISO4217 currency code. Returns "USD" if no match found.
    """
    for c in charmap:
        if c in CURRENCY_CHARMAP:
            return CURRENCY_CHARMAP.get(c)['code']
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
    if not rates:
        # in the unlikely event of an error, invalidate our rates
        # (to try fetching again) and return value unaltered
        _fetch_rates.invalidate()
        return None
    rates = rates["rates"]
    rates["USD"] = 1.0
    try:
        r1 = float(rates.get(valuecode))
        r2 = float(rates.get(targetcode))
    except ValueError:
        # something is very wrong with our data source
        _fetch_rates.invalidate()
        return None
    if not (r1 and r2):
        raise WeasylError("Unexpected")
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

    content = d.engine.execute("""
        SELECT content FROM commishdesc
        WHERE userid = %(id)s
    """, id=userid).scalar()

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
        } for i in query if "a" not in i.settings] + [{
            "classid": i.classid,
            "title": i.title,
            "amount_min": i.amount_min,
            "amount_max": i.amount_max,
            "settings": i.settings,
            "priceid": i.priceid,
        } for i in query if "a" in i.settings],
        "content": content if content else "",
        "tags": [tag.title for tag in preference_tags],
        "opt_out": [tag.title for tag in optout_tags],
    }


def select_commissionable(userid, q, commishclass, min_price, max_price, currency, offset, limit):
    """
    Select a list of artists whom are open for commissions
    and have defined at least one commission class.

    This query sorts primarily by how many matching tags in the "content" field match
    a user's artist tags. Secondarily, it sorts by the user's most recent upload time
    (of any submission that is not hidden or friends-only).
    This way users who are more active on the site will recieve a higher search ranking.
    Ignored users and banned/suspended users will not appear in search results.

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
            cp.settings AS pricesettings,
            MIN(convert.convertedmin) AS convertedmin,
            d.content AS description, s.unixtime,
            tag.tagcount, example.examplecount,
            STRING_AGG(DISTINCT cc.title, ', ') AS class
        FROM profile p

        JOIN login ON p.userid = login.userid

        INNER JOIN commishclass cc ON cc.userid = p.userid
            AND LOWER(cc.title) LIKE %(cclasslike)s

        JOIN commishprice cp ON cp.classid = cc.classid
            AND cp.userid = p.userid
            AND cp.settings NOT LIKE '%%a'

        INNER JOIN (
            SELECT cp.priceid, cp.userid, cp.classid,
            CASE cp.settings
    """]
    # set up the cases to convert currencies from the artist's to the searcher's
    for c in CURRENCY_CHARMAP:
        ratio = currency_ratio(c, currency)
        if not ratio:
            # we assume 1.0 here so a missing ratio doesnt completely mess up
            # the sql query. convertedmin is just for sorting, in event of an
            # error then converted price will be hidden.
            ratio = 1.0
        stmt.append("WHEN '%s' THEN MIN(cp.amount_min) * %f\n" % (c, ratio))

    stmt.append("""
                ELSE MIN(cp.amount_min)
            END AS convertedmin
            FROM commishprice cp
            GROUP BY cp.priceid, cp.userid, cp.classid, cp.settings
        ) AS convert ON convert.priceid = cp.priceid
            AND convert.userid = p.userid
            AND convert.classid = cc.classid

        INNER JOIN (
            SELECT MAX(unixtime) AS unixtime, userid
            FROM submission
            WHERE settings !~ '[hf]'
            GROUP BY userid
        ) AS s ON s.userid = p.userid

        LEFT JOIN commishdesc d ON d.userid = p.userid

        LEFT JOIN (
            SELECT map.targetid, COUNT(tag.tagid) AS tagcount
            FROM searchtag tag
            JOIN artist_preferred_tags map ON map.tagid = tag.tagid
            WHERE tag.title = ANY(%(tags)s)
            GROUP BY map.targetid
        ) AS tag ON tag.targetid = p.userid

        LEFT JOIN (
            SELECT sub.userid, COUNT (sub.submitid) as examplecount
            FROM submission sub
            JOIN searchmapsubmit map ON map.targetid = sub.submitid
            JOIN searchtag tag ON map.tagid = tag.tagid
            WHERE tag.title = ANY(%(tags)s)
            AND sub.rating <= %(rating)s
            AND sub.settings !~ '[hf]'
            GROUP BY sub.userid
        ) AS example ON example.userid = p.userid

        WHERE p.settings ~ '^[os]'
        AND login.settings !~ '[bs]'
        AND p.userid NOT IN (
            SELECT map.targetid
            FROM searchtag tag
            JOIN artist_optout_tags map ON map.tagid = tag.tagid
            WHERE tag.title = ANY(%(tags)s)
            GROUP BY map.targetid
        )
    """)
    tags = q.lower().split()
    if min_price:
        stmt.append("AND convertedmin >= %(min)s ")
    if max_price:
        stmt.append("AND convertedmin <= %(max)s ")
    if userid:
        stmt.append(m.MACRO_IGNOREUSER % (userid, "p"))
    stmt.append("""
        GROUP BY p.userid, cp.settings, d.content, s.unixtime,
        tag.tagcount, example.examplecount
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
            COALESCE(tag.tagcount, 0) DESC, s.unixtime DESC
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
        if info.examplecount and tags:
            terms = ["user:" + info.username] + ["|" + tag for tag in tags]
            dinfo['searchquery'] = "q=" + urllib.quote(" ".join(terms))
        else:
            dinfo['searchquery'] = ""
        return dinfo

    results = [prepare(i) for i in query]
    return results


def create_commission_class(userid, title):
    if not title:
        raise error.WeasylError("titleInvalid")

    classid = d.execute("SELECT MAX(classid) + 1 FROM commishclass WHERE userid = %i", [userid], ["element"])

    try:
        d.execute("INSERT INTO commishclass VALUES (%i, %i, '%s')", [classid if classid else 1, userid, title])
    except error.PostgresError:
        raise error.WeasylError("commishclassExists")


def create_price(userid, price, currency="", settings=""):
    if not price.title:
        raise error.WeasylError("titleInvalid")
    elif price.amount_min > _MAX_PRICE:
        raise error.WeasylError("minamountInvalid")
    elif price.amount_max > _MAX_PRICE:
        raise error.WeasylError("maxamountInvalid")
    elif price.amount_max and price.amount_max < price.amount_min:
        raise error.WeasylError("maxamountInvalid")
    elif not d.execute("SELECT EXISTS (SELECT 0 FROM commishclass WHERE (classid, userid) = (%i, %i))",
                       [price.classid, userid], ["bool"]):
        raise error.WeasylError("classidInvalid")
    elif not price.classid:
        raise error.WeasylError("classidInvalid")

    # Settings are at most one currency class, and optionally an 'a' to indicate an add-on price.
    # TODO: replace these character codes with an enum.
    settings = "%s%s" % ("".join(i for i in currency if i in CURRENCY_CHARMAP)[:1],
                         "a" if "a" in settings else "")

    # TODO: should have an auto-increment ID
    priceid = d.execute("SELECT MAX(priceid) + 1 FROM commishprice WHERE userid = %i", [userid], ["element"])

    try:
        d.execute(
            "INSERT INTO commishprice VALUES (%i, %i, %i, '%s', %i, %i, '%s')",
            [priceid if priceid else 1, price.classid, userid, price.title, price.amount_min, price.amount_max, settings])
    except error.PostgresError:
        return error.WeasylError("titleExists")


def edit_class(userid, commishclass):

    if not commishclass.title:
        raise error.WeasylError("titleInvalid")

    try:
        d.execute("UPDATE commishclass SET title = '%s' WHERE (classid, userid) = (%i, %i)",
                  [commishclass.title, commishclass.classid, userid])
    except error.PostgresError:
        raise error.WeasylError("titleExists")


def edit_price(userid, price, currency="", settings="", edit_prices=False, edit_settings=False):
    currency = "".join(i for i in currency if i in CURRENCY_CHARMAP)
    settings = "".join(i for i in settings if i in "a")

    query = d.execute("SELECT amount_min, amount_max, settings, classid FROM commishprice"
                      " WHERE (priceid, userid) = (%i, %i)", [price.priceid, userid], options="single")

    if not query:
        raise error.WeasylError("priceidInvalid")
    elif price.amount_min > _MAX_PRICE:
        raise error.WeasylError("minamountInvalid")
    elif price.amount_max > _MAX_PRICE:
        raise error.WeasylError("maxamountInvalid")
    elif price.amount_max and price.amount_max < price.amount_min:
        raise error.WeasylError("maxamountInvalid")

    argv = []
    statement = ["UPDATE commishprice SET "]

    if price.title:
        statement.append("%s title = '%%s'" % ("," if argv else ""))
        argv.append(price.title)

    if edit_prices:
        if price.amount_min != query[0]:
            statement.append("%s amount_min = %%i" % ("," if argv else ""))
            argv.append(price.amount_min)

        if price.amount_max != query[1]:
            statement.append("%s amount_max = %%i" % ("," if argv else ""))
            argv.append(price.amount_max)

    if edit_settings:
        statement.append("%s settings = '%%s'" % ("," if argv else ""))
        argv.append("%s%s" % (currency, settings))

    if not argv:
        return

    statement.append(" WHERE (priceid, userid) = (%i, %i)")
    argv.extend([price.priceid, userid])

    d.execute("".join(statement), argv)


def edit_content(userid, content):
    if not d.execute("UPDATE commishdesc SET content = '%s' WHERE userid = %i RETURNING userid",
                     [content, userid], ["element"]):
        d.execute("INSERT INTO commishdesc VALUES (%i, '%s')", [userid, content])


def remove_class(userid, classid):
    d.execute("DELETE FROM commishclass WHERE (classid, userid) = (%i, %i)", [d.get_int(classid), userid])


def remove_price(userid, priceid):
    d.execute("DELETE FROM commishprice WHERE (priceid, userid) = (%i, %i)", [d.get_int(priceid), userid])

from __future__ import absolute_import

from weasyl.cache import region
from weasyl.error import WeasylError
import re
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
    :return: The converted amount
    """
    valuecode = _charmap_to_currency_code(valuecode)
    targetcode = _charmap_to_currency_code(targetcode)
    if targetcode == valuecode:
        return value
    rates = _fetch_rates()
    if not rates:
        # in the unlikely event of an error, invalidate our rates
        # (to try fetching again) and return value unaltered
        _fetch_rates.invalidate()
        return value
    rates = rates["rates"]
    rates["USD"] = 1.0
    r1 = rates.get(valuecode)
    r2 = rates.get(targetcode)
    if not (r1 and r2):
        raise WeasylError("Unexpected")
    return value * r2 / r1


def select_list(userid):
    query = d.engine.execute("SELECT classid, title, amount_min, amount_max, settings, priceid FROM commishprice"
                             " WHERE userid = %(userid)s ORDER BY classid, title", userid=userid)
    classes = d.engine.execute("SELECT classid, title FROM commishclass WHERE userid = %(id)s ORDER BY title", id=userid)
    content = d.engine.execute("SELECT content FROM commishdesc WHERE userid = %(id)s", id=userid).scalar()
    tags = d.engine.execute("SELECT DISTINCT tag.title, sma.settings FROM searchtag tag "
                            "join searchmapartist sma on sma.tagid = tag.tagid "
                            "join login l on l.userid = sma.targetid "
                            "where l.userid = %(userid)s", userid=userid)
    tags_extract = [{"t": i.title, "s": i.settings} for i in tags]
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
        "tags": [i["t"] for i in tags_extract if 'n' not in i["s"]],
        "no_draw": [i["t"] for i in tags_extract if 'n' in i["s"]],
    }


def select_commissionable(userid, q, commishclass, min_price, max_price, currency, offset, limit):
    """
    Select a list of artists whom are open for commissions
    and have defined at least one commission class.

    TODO:
        - relax the requirement for setting up commission classes
        - don't return results that are on the searching user's ignore list
        - find a way to have max_price and min_price work with currency conversions
        - redo the entire thing when (if) commissioninfo has (gets) a better schema
        - don't show results for banned or suspended users

    :param userid: The user making the request
    :param q: Weight artists with "preferred content" tags that match these higher
    :param commishclass: Only return artists with at least one commission class containing this keyword
    :param min_price: Do not return artists with a minimum price below this value
    :param max_price: Do not return artists with a minimum price above this value
    :param currency: The single-character currency code to convert the returned results in,
                     as defined in commishprice.settings
    :param offset: Results set offset for pagination. Must be a positive Number
    :param limit: max number of results to return
    :return: The resulting list of artists & their commission info
    """
    # in this proof of concept, sort users by their most recent upload
    # this has the benefit of displaying more active users most prominently
    stmt = [
        """SELECT p.userid, p.username, p.settings,
                MIN(cp.amount_min) AS pricemin,
                GREATEST(MAX(cp.amount_max), MAX(cp.amount_min)) AS pricemax,
                cp.settings AS pricesettings,
                d.content AS description, s.unixtime,
                tag.tagcount, example.examplecount
            FROM profile p

            INNER JOIN commishclass cc ON cc.userid = p.userid
                AND lower(cc.title) LIKE %(cclass)s

            INNER JOIN (
                SELECT MAX(unixtime) as unixtime, userid
                FROM submission
                GROUP BY userid
            ) AS s ON s.userid = p.userid

            JOIN commishprice cp ON cp.classid = cc.classid
                AND cp.userid = p.userid
                AND cp.settings NOT LIKE '%%a'

            JOIN commishdesc d ON d.userid = p.userid

            LEFT JOIN (
                SELECT map.targetid, COUNT(tag.tagid) AS tagcount
                FROM searchtag tag
                JOIN searchmapartist map ON map.tagid = tag.tagid
                WHERE tag.title = ANY(%(tags)s)
                GROUP BY map.targetid
            ) AS tag ON tag.targetid = p.userid

            LEFT JOIN (
                SELECT sub.userid, COUNT (sub.submitid) as examplecount
                FROM submission sub
                JOIN searchmapsubmit map ON map.targetid = sub.submitid
                JOIN searchtag tag ON map.tagid = tag.tagid
                WHERE tag.title = ANY(%(tags)s)
                AND rating <= %(rating)s
                GROUP BY sub.userid
            ) AS example ON example.userid = p.userid
            
            WHERE p.settings ~ '[os]..?'
            AND p.userid NOT IN (
                SELECT map.targetid
                FROM searchtag tag
                JOIN searchmapartist map on map.tagid = tag.tagid
                WHERE tag.title = ANY(%(tags)s)
                AND map.settings ~ 'n'
                GROUP BY map.targetid
            ) """
    ]
    if min_price:
        stmt.append("AND cp.amount_min >= %(min)s ")
    if max_price:
        stmt.append("AND cp.amount_min <= %(max)s ")
    stmt.append("GROUP BY p.userid, cp.settings, d.content, s.unixtime, tag.tagcount, example.examplecount "
                "ORDER BY COALESCE(tag.tagcount, 0) DESC, s.unixtime DESC "
                "LIMIT %(limit)s OFFSET %(offset)s")
    tags = q.lower().split()
    if commishclass:
        tags.append(commishclass)
    commishclass = "%" + commishclass + "%"
    max_rating = d.get_rating(userid)
    query = d.engine.execute("".join(stmt), limit=limit, min=min_price,
                             max=max_price, cclass=commishclass, tags=tags,
                             rating=max_rating, offset=offset)

    def prepare(info):
        dinfo = dict(info)
        dinfo['localmin'] = convert_currency(info.pricemin, info.pricesettings, currency)
        dinfo['localmax'] = convert_currency(info.pricemax, info.pricesettings, currency)
        if info.examplecount and tags:
            dinfo['searchquery'] = "q=user%3A" + info.username + "+%7C" + "+%7C".join(tags)
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
    settings = "%s%s" % ("".join(i for i in currency if i in "epycmufzn")[:1],
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
    currency = "".join(i for i in currency if i in "epycmufzn")
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

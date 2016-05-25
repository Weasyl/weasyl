# commishinfo.py

import error
import define as d
from decimal import Decimal
from weasyl.cache import region
from weasyl.error import WeasylError
import re

_MAX_PRICE = 99999999

CURRENCY_PRECISION = 2

# map database charset to ISO4217 currency codes
# USD is default & is indicated by the existence of no other matching value
_CURRENCY_CHARMAP = {
    "e": "EUR",
    "p": "GBP",
    "y": "JPY",
    "c": "CAD",
    "m": "MXN",
    "u": "AUD",
}


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


@region.cache_on_arguments(expiration_time=60*60*24)
def _fetch_rates():
    try:
        return d.http_get("http://api.fixer.io/latest?base=USD").json()
    except:
        return None


def _charmap_to_currency_code(charmap):
    for c in charmap:
        if c in _CURRENCY_CHARMAP:
            return _CURRENCY_CHARMAP.get(c)
    return "USD"


def convert_currency(value, valuecode, targetcode):
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
    return value * r2/r1


def select_list(userid):
    query = d.execute("SELECT classid, title, amount_min, amount_max, settings, priceid FROM commishprice"
                      " WHERE userid = %i ORDER BY classid, title", [userid])

    content = d.execute("SELECT content FROM commishdesc WHERE userid = %i", [userid], ["element"])

    return {
        "class": [{
            "classid": i[0],
            "title": i[1],
        } for i in d.execute("SELECT classid, title FROM commishclass WHERE userid = %i ORDER BY title", [userid])],
        "price": [{
            "classid": i[0],
            "title": i[1],
            "amount_min": i[2],
            "amount_max": i[3],
            "settings": i[4],
            "priceid": i[5],
        } for i in query if "a" not in i[4]] + [{
            "classid": i[0],
            "title": i[1],
            "amount_min": i[2],
            "amount_max": i[3],
            "settings": i[4],
            "priceid": i[5],
        } for i in query if "a" in i[4]],
        "content": content if content else "",
    }


def select_commissionable(userid, query, min_price, max_price, currency, limit,):
    """
    TODO write a description
    :param userid:
    :param limit:
    :return:
    """
    # in this proof of concept, sort users by their most recent upload
    # this has the benefit of displaying more active users most prominently
    # TODO properly format this
    stmt = [
        "SELECT DISTINCT p.userid, p.username, p.settings, s.unixtime, "
        "prices.pricemin, prices.pricemax, priceconfig.settings AS pricesettings, "
        "d.content AS description "
        "FROM profile p "
        "JOIN submission s ON s.userid = p.userid "
        "JOIN (SELECT cp.userid, MIN(cp.amount_min) AS pricemin, "
        "GREATEST(MAX(cp.amount_max), MAX(cp.amount_min)) AS pricemax "
        "FROM commishprice cp "
        "WHERE cp.settings NOT LIKE '%%a' "
        "GROUP BY cp.userid) "
        "AS prices ON prices.userid = p.userid "
        "JOIN commishdesc d ON d.userid = p.userid "
        "LEFT JOIN (SELECT DISTINCT cp.settings, cp.userid, cp.amount_min "
        "FROM commishprice cp "
        "WHERE cp.settings NOT LIKE '%%a') "
        "AS priceconfig ON priceconfig.userid = p.userid "
        "AND priceconfig.amount_min = prices.pricemin "
        "WHERE p.settings ~ '[os]..?' "
        "AND s.unixtime = (select MAX(s.unixtime) FROM submission s WHERE s.userid = p.userid) "
    ]
    if min_price:
        stmt.append("AND prices.pricemin >= %(min)s ")
    if max_price:
        stmt.append("AND prices.pricemin <= %(max)s ")
    stmt.append("ORDER BY s.unixtime DESC ")
    stmt.append("LIMIT %(limit)s ")
    query = d.engine.execute("".join(stmt), limit=limit, min=min_price, max=max_price)

    def prepare(info):
        dinfo = dict(info)
        dinfo['localmin'] = convert_currency(info.pricemin, info.pricesettings, currency)
        dinfo['localmax'] = convert_currency(info.pricemax, info.pricesettings, currency)

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
    settings = "%s%s" % ("".join(i for i in currency if i in "epycmu")[:1],
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
    currency = "".join(i for i in currency if i in "epycmu")
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

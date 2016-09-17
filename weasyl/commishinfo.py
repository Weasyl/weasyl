from __future__ import absolute_import

import re
from decimal import Decimal

from weasyl import define as d
from weasyl import error

_MAX_PRICE = 99999999

CURRENCY_PRECISION = 2


def convert_currency(target):
    """
    Return the target string as a price integer; for example, "$1.23" becomes
    123 which can then be stored in the database.
    """
    if not target:
        return 0
    # strip everything but digits and a decimal point
    digits = re.sub("[^0-9.]", "", target)
    return int(Decimal(digits) * (10 ** CURRENCY_PRECISION))


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

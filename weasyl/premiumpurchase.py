from __future__ import absolute_import

from libweasyl import security
from weasyl import define, emailer, error


def append(db, email, terms):
    token = security.generate_key(40)
    email = emailer.normalize_address(email)

    if not email:
        raise error.WeasylError("emailInvalid")

    define.execute(db, "INSERT INTO premiumpurchase VALUES ('%s', '%s', %i)", [token, email, terms])

    emailer.append([email], None, "Weasyl Premium Verification",
                   define.render("email/verify_premium.html", [token, terms]))


def verify(db, userid, token):
    # Select purchased terms
    terms = define.execute(db, "SELECT terms FROM premiumpurchase WHERE token = '%s'", [token], ["element"])

    if not terms:
        raise error.WeasylError("tokenInvalid")

    # Select current terms
    current = define.execute(db, "SELECT terms FROM userpremium WHERE userid = %i", [userid], ["element"])

    # Update premium status
    if current:
        define.execute(db, "UPDATE userpremium SET terms = terms + %i WHERE userid = %i", [terms, userid])
    else:
        define.execute(db, "INSERT INTO userpremium VALUES (%i, %i, %i)", [userid, define.get_time(), terms])
        define.execute(db, "UPDATE profile SET config = config || 'd' WHERE userid = %i AND config !~ 'd'", [userid])

    define.execute(db, "DELETE FROM premiumpurchase WHERE token = '%s'", [token])

import datetime

import arrow
import pytest
from weasyl.test import db_utils
from weasyl import commishinfo, define as d, orm, profile, searchtag


@pytest.mark.usefixtures('db', 'cache')
@pytest.mark.parametrize(['args', 'result_order'], [
    # test that the broadest terms return all users in the right order
    ({
        'q': "",
        'commishclass': "",
        'min_price': None,
        'max_price': None,
        'currency': '',
    }, ["u2", "u3", "u4", "u5", "u6"]),
    # test searching for a specific commish class
    ({
        'q': "",
        'commishclass': "sketch",
        'min_price': None,
        'max_price': None,
        'currency': '',
    }, ["u5"]),
    # test that content tags affect placement and exclusion in results
    ({
        'q': "cat",
        'commishclass': "",
        'min_price': None,
        'max_price': None,
        'currency': '',
    }, ["u5", "u2", "u3", "u6"]),
    # test min prices
    ({
        'q': "",
        'commishclass': "",
        'min_price': 5000,
        'max_price': None,
        'currency': '',
    }, ["u6"]),
    # test max prices
    ({
        'q': "",
        'commishclass': "",
        'min_price': None,
        'max_price': 2000,
        'currency': '',
    }, ["u2", "u3", "u4", "u5"]),
])
def test_commish_search(args, result_order):
    # searcher
    u1 = db_utils.create_user(username="searcher")

    # user open for commissions
    create_commish_searchable_user("u2", submittime=arrow.utcnow())

    # user sometimes open for commissions (should behave same as above)
    create_commish_searchable_user("u3", commish_status='s',
                                   submittime=arrow.utcnow() - datetime.timedelta(days=1))

    # user open for commissions, with blacklisted tags
    u4 = create_commish_searchable_user("u4", submittime=arrow.utcnow() - datetime.timedelta(days=2))
    searchtag.set_commission_optout_tags(userid=u4, tag_names={'cat'})

    # user with a different commish class and a preference tag
    u5 = create_commish_searchable_user("u5", commishclass="sketch",
                                        submittime=arrow.utcnow() - datetime.timedelta(days=3))
    searchtag.set_commission_preferred_tags(userid=u5, tag_names={'cat'})

    # user with a different price
    create_commish_searchable_user("u6", minprice="100.0", maxprice="100.0",
                                   submittime=arrow.utcnow() - datetime.timedelta(days=4))

    results = commishinfo.select_commissionable(userid=u1,
                                                limit=10,
                                                offset=0,
                                                **args)
    rids = [r['username'] for r in results]
    assert rids == result_order


@pytest.mark.usefixtures('db', 'cache')
def test_commish_search_invalid():
    # searcher
    u1 = db_utils.create_user(username="searcher")

    # user not open for commissions, but with submissions and commish classes defined
    create_commish_searchable_user("u2", commish_status='c')

    # user open for commission but without any commish classes
    u3 = create_commish_searchable_user("u3")
    classid = commishinfo.select_list(u3)["class"][0]["classid"]
    commishinfo.remove_class(u3, classid)

    # user meets all requirements, but is suspended
    u4 = create_commish_searchable_user("u4")
    db_utils.create_suspenduser(u4, "", d.get_time() + 604800)

    # user meets all requirements, but is banned
    u5 = create_commish_searchable_user("u5")
    db_utils.create_banuser(u5, "")

    # user meets all requirements, but is ignored by searching user
    u6 = create_commish_searchable_user("u6")
    db_utils.create_ignoreuser(u1, u6)

    results = commishinfo.select_commissionable(userid=u1,
                                                limit=10,
                                                offset=0,
                                                q="",
                                                commishclass="",
                                                min_price=None,
                                                max_price=None,
                                                currency='')
    assert not results


def create_commish_searchable_user(username, commish_status='o', commishclass='badge',
                                   minprice="10.00", maxprice="15.00", currency='', submittime=arrow.get(1)):
    user = db_utils.create_user(username=username)
    profile.edit_profile_settings(
        userid=user,
        set_trade=profile.EXCHANGE_SETTING_NOT_ACCEPTING,
        set_request=profile.EXCHANGE_SETTING_NOT_ACCEPTING,
        set_commission=profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, commish_status)
    )
    commishinfo.create_commission_class(user, commishclass)
    classid = commishinfo.select_list(user)["class"][0]["classid"]
    assert classid

    price = orm.CommishPrice()
    price.title = "test price"
    price.classid = classid
    price.amount_min = commishinfo.parse_currency(minprice)
    price.amount_max = commishinfo.parse_currency(maxprice)
    commishinfo.create_price(user, price, currency)

    db_utils.create_submission(user, unixtime=submittime)

    return user

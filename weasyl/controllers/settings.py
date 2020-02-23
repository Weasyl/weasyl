from __future__ import absolute_import

import os

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

import libweasyl.ratings as ratings
from libweasyl import staff

from weasyl.controllers.decorators import disallow_api, login_required, token_checked
from weasyl.error import WeasylError
from weasyl import (
    api, avatar, banner, blocktag, collection, commishinfo,
    define, emailer, folder, followuser, frienduser, ignoreuser,
    index, login, oauth2, profile, searchtag, thumbnail, useralias, orm)


# Control panel functions
@view_config(route_name="control", renderer='/control/control.jinja2')
@login_required
def control_(request):
    return {
        'premium': define.get_premium(request.userid),
        'vouched': define.is_vouched_for(request.userid),
        'title': "Settings"
    }


@view_config(route_name="control_uploadavatar", request_method="POST")
@login_required
@token_checked
def control_uploadavatar_(request):
    form = request.web_input(image="")

    manage = avatar.upload(request.userid, form.image)
    if manage:
        raise HTTPSeeOther(location="/manage/avatar")
    else:
        raise HTTPSeeOther(location="/control")


@view_config(route_name="control_editprofile", renderer='/control/edit_profile.jinja2', request_method="GET")
@login_required
def control_editprofile_get_(request):
    userinfo = profile.select_userinfo(request.userid)
    return {
        'profile': profile.select_profile(request.userid, commish=False),
        'userinfo': userinfo,
        'title': "Edit Profile",
        'options': ["typeahead"]
    }


@view_config(route_name="control_editprofile", renderer='/control/edit_profile.jinja2', request_method="POST")
@login_required
@token_checked
def control_editprofile_put_(request):
    form = request.web_input(
        full_name="", catchphrase="",
        profile_text="", set_commish="", set_trade="", set_request="",
        set_stream="", stream_url="", stream_text="", show_age="",
        gender="", country="", profile_display="", site_names=[], site_values=[])

    if len(form.site_names) != len(form.site_values):
        raise WeasylError('Unexpected')

    if 'more' in form:
        form.sorted_user_links = [(name, [value]) for name, value in zip(form.site_names, form.site_values)]
        form.settings = form.set_commish + form.set_trade + form.set_request
        form.config = form.profile_display
        return {'profile': form, 'userinfo': form, 'title': "Edit Profile", 'options': ["typeahead"]}

    p = orm.Profile()
    p.full_name = form.full_name
    p.catchphrase = form.catchphrase
    p.profile_text = form.profile_text
    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, form.set_trade)
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, form.set_request)
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, form.set_commish)
    profile.edit_profile(request.userid, p, set_trade=set_trade,
                         set_request=set_request, set_commission=set_commission,
                         profile_display=form.profile_display)

    profile.edit_userinfo(request.userid, form)

    raise HTTPSeeOther(location="/control")


@view_config(route_name="control_editcommissionsettings", renderer='/control/edit_commissionsettings.jinja2', request_method="GET")
@login_required
def control_editcommissionsettings_(request):
    return {
        'query': commishinfo.select_list(request.userid),
        'currencies': commishinfo.CURRENCY_CHARMAP,
        'presets': commishinfo.PRESET_COMMISSION_CLASSES,
        'profile': profile.select_profile(request.userid),
        'title': "Edit Commission Settings"
    }


@view_config(route_name="control_editcommishinfo", request_method="POST")
@login_required
@token_checked
def control_editcommishinfo_(request):
    form = request.web_input(content="", set_commish="", set_trade="", set_request="")
    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, form.set_trade)
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, form.set_request)
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, form.set_commish)

    profile.edit_profile_settings(request.userid, set_trade, set_request, set_commission)
    commishinfo.edit_content(request.userid, form.content)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_createcommishclass", request_method="POST")
@login_required
@token_checked
def control_createcommishclass_(request):
    form = request.web_input(title="", titlepreset="", price_title="", min_amount="", max_amount="", currency="")
    title = form.title or form.titlepreset
    form.currency = form.currency.replace("$", "")

    classid = commishinfo.create_commission_class(request.userid, title.strip())
    # Try to create a base price for it. If we fail, try to clean up the class.
    try:
        price = orm.CommishPrice()
        price.title = form.price_title.strip()
        price.classid = classid
        price.amount_min = commishinfo.parse_currency(form.min_amount)
        price.amount_max = commishinfo.parse_currency(form.max_amount)
        commishinfo.create_price(request.userid, price, currency=form.currency)
    except WeasylError as we:
        commishinfo.remove_class(request.userid, classid)
        raise we
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_editcommishclass", request_method="POST")
@login_required
@token_checked
def control_editcommishclass_(request):
    form = request.web_input(classid="", title="")

    commishclass = orm.CommishClass()
    commishclass.title = form.title.strip()
    commishclass.classid = define.get_int(form.classid)
    commishinfo.edit_class(request.userid, commishclass)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_removecommishclass", request_method="POST")
@login_required
@token_checked
def control_removecommishclass_(request):
    classid = define.get_int(request.params.get('classid', ""))

    if not classid:
        raise WeasylError("classidInvalid")

    commishinfo.remove_class(request.userid, classid)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_createcommishprice", request_method="POST")
@login_required
@token_checked
def control_createcommishprice_(request):
    form = request.web_input(title="", classid="", min_amount="", max_amount="", currency="", settings="")
    form.currency = form.currency.replace("$", "")

    price = orm.CommishPrice()
    price.title = form.title.strip()
    price.classid = define.get_int(form.classid)
    price.amount_min = commishinfo.parse_currency(form.min_amount)
    price.amount_max = commishinfo.parse_currency(form.max_amount)
    commishinfo.create_price(request.userid, price, currency=form.currency,
                             settings=form.settings)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_editcommishprice", request_method="POST")
@login_required
@token_checked
def control_editcommishprice_(request):
    form = request.web_input(priceid="", title="", min_amount="", max_amount="", currency="", settings="")
    form.currency = form.currency.replace("$", "")

    price = orm.CommishPrice()
    price.title = form.title.strip()
    price.priceid = define.get_int(form.priceid)
    price.amount_min = commishinfo.parse_currency(form.min_amount)
    price.amount_max = commishinfo.parse_currency(form.max_amount)
    edit_prices = bool(price.amount_min or price.amount_max)
    commishinfo.edit_price(request.userid, price, currency=form.currency,
                           settings=form.settings, edit_prices=edit_prices)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_removecommishprice", request_method="POST")
@login_required
@token_checked
def control_removecommishprice_(request):
    priceid = define.get_int(request.params.get('priceid', ""))

    if not priceid:
        raise WeasylError("priceidInvalid")

    commishinfo.remove_price(request.userid, priceid)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@view_config(route_name="control_username", renderer='/control/username.jinja2', request_method="GET")
@login_required
def control_username_get_(request):
    latest_change = define.engine.execute(
        "SELECT username, active, extract(epoch from now() - replaced_at)::int8 AS seconds"
        " FROM username_history"
        " WHERE userid = %(user)s"
        " AND NOT cosmetic"
        " ORDER BY historyid DESC LIMIT 1",
        user=request.userid,
    ).first()

    if latest_change is None:
        existing_redirect = None
        days = None
    else:
        existing_redirect = latest_change.username if latest_change.active else None
        days = latest_change.seconds // (3600 * 24)

    return {
        'username': define.get_display_name(request.userid),
        'existing_redirect': existing_redirect,
        'insufficient_days': days if days < 30 else None,
        'title': 'Change Username'
    }


@view_config(route_name="control_username", renderer='/control/username.jinja2', request_method="POST")
@login_required
@token_checked
def control_username_post_(request):
    if request.POST['do'] == 'change':
        login.change_username(
            acting_user=request.userid,
            target_user=request.userid,
            bypass_limit=False,
            new_username=request.POST['new_username'],
        )

        return {
            'error': 'Your username has been changed.',
            'title': 'Change Username'
        }

    elif request.POST['do'] == 'release':
        login.release_username(
            define.engine,
            acting_user=request.userid,
            target_user=request.userid,
        )
        return {
            'error': 'Your old username has been released.',
            'title': 'Change Username'
        }
    else:
        raise WeasylError("Unexpected")


@login_required
@disallow_api
def control_editemailpassword_get_(request):
    return {'email': profile.select_manage(request.userid), 'title': "Edit Password and Email Address"}


@view_config(route_name="control_editemailpassword", renderer='/control/edit_emailpassword.jinja2', request_method="POST")
@login_required
@disallow_api
@token_checked
def control_editemailpassword_post_(request):
    form = request.web_input(newemail="", newemailcheck="", newpassword="", newpasscheck="", password="")

    newemail = emailer.normalize_address(form.newemail)
    newemailcheck = emailer.normalize_address(form.newemailcheck)

    # Check if the email was invalid; Both fields must be valid (not None), and have the form fields set
    if not newemail and not newemailcheck and form.newemail != "" and form.newemailcheck != "":
        raise WeasylError("emailInvalid")

    return_message = profile.edit_email_password(
        request.userid, form.username, form.password, newemail, newemailcheck,
        form.newpassword, form.newpasscheck
    )

    if not return_message:  # No changes were made
        return {'message': "No changes were made to your account."}
    else:  # Changes were made, so inform the user of this
        return {'message': "**Success!** " + return_message}


@view_config(route_name="control_editpreferences", renderer='/control/edit_preferences.jinja2', request_method="GET")
@login_required
def control_editpreferences_get_(request):
    config = define.get_config(request.userid)
    current_rating, current_sfw_rating = define.get_config_rating(request.userid)
    age = profile.get_user_age(request.userid)
    allowed_ratings = ratings.get_ratings_for_age(age)
    jsonb_settings = define.get_profile_settings(request.userid)
    return {
        'config': config,
        'jsonb_settings': jsonb_settings,
        'current_rating': current_rating,
        'current_sfw_rating': current_sfw_rating,
        'age': age,
        'allowed_ratings': allowed_ratings,
        'timezone': request.weasyl_session.timezone.timezone,
        'timezones': define.timezones(),
        'title': "Site Preferences"
    }


@view_config(route_name="control_editpreferences", renderer='/control/edit_preferences.jinja2', request_method="POST")
@login_required
@token_checked
def control_editpreferences_post_(request):
    form = request.web_input(
        rating="", sfwrating="", custom_thumbs="", tagging="",
        hideprofile="", hidestats="", hidefavorites="", hidefavbar="",
        shouts="", notes="", filter="",
        follow_s="", follow_c="", follow_f="", follow_t="",
        follow_j="", timezone="", twelvehour="")

    rating = ratings.CODE_MAP[define.get_int(form.rating)]
    jsonb_settings = define.get_profile_settings(request.userid)
    jsonb_settings.disable_custom_thumbs = form.custom_thumbs == "disable"
    jsonb_settings.max_sfw_rating = define.get_int(form.sfwrating)

    preferences = profile.Config()
    preferences.twelvehour = bool(form.twelvehour)
    preferences.rating = rating
    preferences.tagging = bool(form.tagging)
    preferences.hideprofile = bool(form.hideprofile)
    preferences.hidestats = bool(form.hidestats)
    preferences.hidefavorites = bool(form.hidefavorites)
    preferences.hidefavbar = bool(form.hidefavbar)
    preferences.shouts = ("friends_only" if form.shouts == "x" else
                          "staff_only" if form.shouts == "w" else "anyone")
    preferences.notes = ("friends_only" if form.notes == "z" else
                         "staff_only" if form.notes == "y" else "anyone")
    preferences.filter = bool(form.filter)
    preferences.follow_s = bool(form.follow_s)
    preferences.follow_c = bool(form.follow_c)
    preferences.follow_f = bool(form.follow_f)
    preferences.follow_t = bool(form.follow_t)
    preferences.follow_j = bool(form.follow_j)

    profile.edit_preferences(request.userid, timezone=form.timezone,
                             preferences=preferences, jsonb_settings=jsonb_settings)
    # release the cache on the index page in case the Maximum Viewable Content Rating changed.
    index.template_fields.invalidate(request.userid)
    raise HTTPSeeOther(location="/control")


@view_config(route_name="control_createfolder", request_method="POST")
@login_required
@token_checked
def control_createfolder_(request):
    form = request.web_input(title="", parentid="")

    folder.create(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@view_config(route_name="control_renamefolder", request_method="POST")
@login_required
@token_checked
def control_renamefolder_(request):
    form = request.web_input(folderid="", title="")

    if define.get_int(form.folderid):
        folder.rename(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@view_config(route_name="control_removefolder", request_method="POST")
@login_required
@token_checked
def control_removefolder_(request):
    form = request.web_input(folderid="")
    form.folderid = define.get_int(form.folderid)

    if form.folderid:
        folder.remove(request.userid, form.folderid)
    raise HTTPSeeOther(location="/manage/folders")


@view_config(route_name="control_editfolder", renderer='/manage/folder_options.jinja2', request_method="GET")
@login_required
def control_editfolder_get_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        raise WeasylError('permission')

    return {'info': folder.select_info(folderid), 'title': "Edit Folder Options"}


@view_config(route_name="control_editfolder", renderer='/manage/folder_options.jinja2', request_method="POST")
@login_required
@token_checked
def control_editfolder_post_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        raise WeasylError('permission')

    form = request.web_input(settings=[])
    folder.update_settings(folderid, form.settings)
    raise HTTPSeeOther(location='/manage/folders')


@view_config(route_name="control_movefolder", request_method="POST")
@login_required
@token_checked
def control_movefolder_(request):
    form = request.web_input(folderid="", parentid="")
    form.folderid = define.get_int(form.folderid)

    if form.folderid and define.get_int(form.parentid) >= 0:
        folder.move(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@view_config(route_name="control_ignoreuser", request_method="POST")
@login_required
@token_checked
def control_ignoreuser_(request):
    form = request.web_input(username="")

    ignoreuser.insert(request.userid, define.get_userid_list(form.username))
    raise HTTPSeeOther(location="/manage/ignore")


@view_config(route_name="control_unignoreuser", request_method="POST")
@login_required
@token_checked
def control_unignoreuser_(request):
    form = request.web_input(username="")

    ignoreuser.remove(request.userid, define.get_userid_list(form.username))
    raise HTTPSeeOther(location="/manage/ignore")


@view_config(route_name="control_streaming", renderer='/control/edit_streaming.jinja2', request_method="GET")
@login_required
def control_streaming_get_(request):
    form = request.web_input(target='')
    if form.target and request.userid not in staff.MODS:
        raise WeasylError('permission')
    elif form.target:
        target = define.get_int(form.target)
    else:
        target = request.userid

    return {
        'profile': profile.select_profile(target, commish=False),
        'target': form.target,
        'title': "Edit Streaming Settings"
    }


@view_config(route_name="control_streaming", renderer='/control/edit_streaming.jinja2', request_method="POST")
@login_required
@token_checked
def control_streaming_post_(request):
    form = request.web_input(target="", set_stream="", stream_length="", stream_url="", stream_text="")

    if form.target and request.userid not in staff.MODS:
        raise WeasylError('permission')

    if form.target:
        target = int(form.target)
    else:
        target = request.userid

    stream_length = define.clamp(define.get_int(form.stream_length), 0, 360)
    p = orm.Profile()
    p.stream_text = form.stream_text
    p.stream_url = define.text_fix_url(form.stream_url.strip())
    set_stream = form.set_stream

    profile.edit_streaming_settings(request.userid, target, p,
                                    set_stream=set_stream,
                                    stream_length=stream_length)

    if form.target:
        target_username = define.get_sysname(define.get_display_name(target))
        raise HTTPSeeOther(location="/modcontrol/manageuser?name=" + target_username)
    else:
        raise HTTPSeeOther(location="/control")


@view_config(route_name="control_apikeys", renderer='/control/edit_apikeys.jinja2', request_method="GET")
@login_required
@disallow_api
def control_apikeys_get_(request):
    return {
        'api_keys': api.get_api_keys(request.userid),
        'consumers':oauth2.get_consumers_for_user(request.userid),
        'title': "API Keys"
    }


@view_config(route_name="control_apikeys", renderer='/control/edit_apikeys.jinja2', request_method="POST")
@login_required
@disallow_api
@token_checked
def control_apikeys_post_(request):
    form = request.web_input(**{'delete-api-keys': [], 'revoke-oauth2-consumers': []})

    if form.get('add-api-key'):
        api.add_api_key(request.userid, form.get('add-key-description'))
    if form.get('delete-api-keys'):
        api.delete_api_keys(request.userid, form['delete-api-keys'])
    if form.get('revoke-oauth2-consumers'):
        oauth2.revoke_consumers_for_user(request.userid, form['revoke-oauth2-consumers'])

    raise HTTPSeeOther(location="/control/apikeys")


@view_config(route_name="control_tagrestrictions", renderer='/control/edit_tagrestrictions.jinja2', request_method="GET")
@login_required
def control_tagrestrictions_get_(request):
    return {
        'tags': sorted(searchtag.query_user_restricted_tags(request.userid)),
        'title': "Edit Community Tagging Restrictions"
    }


@view_config(route_name="control_tagrestrictions", renderer='/control/edit_tagrestrictions.jinja2', request_method="POST")
@login_required
@token_checked
def control_tagrestrictions_post_(request):
    tags = searchtag.parse_restricted_tags(request.params["tags"])
    searchtag.edit_user_tag_restrictions(request.userid, tags)

    raise HTTPSeeOther(location=request.route_path('control_tagrestrictions'))


@view_config(route_name="manage_folders", renderer='/manage/folders.jinja2', request_method="GET")
@login_required
def manage_folders_(request):
    return {'folders': folder.select_list(request.userid, "drop/all"), 'title': "Submission Folders"}


@view_config(route_name="control_following", renderer='/manage/following_list.jinja2', request_method="GET")
@login_required
def manage_following_get_(request):
    form = request.web_input(backid="", nextid="")
    form.backid = define.get_int(form.backid)
    form.nextid = define.get_int(form.nextid)

    return {
        'query': followuser.manage_following(request.userid, 44, backid=form.backid, nextid=form.nextid),
        'title': "Users You Follow"
    }


@view_config(route_name="control_manage_follow", renderer='/manage/following_user.jinja2', request_method="GET")
@login_required
def manage_follow_get_(request):
    userid = define.get_int(request.matchdict['userid'])

    return {
        'profile': profile.select_profile(userid, avatar=True),
        'settings': followuser.select_settings(request.userid, userid),
        'title': "Followed User"
    }


@view_config(route_name="control_manage_follow", renderer='/manage/following_user.jinja2', request_method="POST")
@login_required
@token_checked
def manage_follow_post_(request):
    form = request.web_input(userid="", submit="", collect="", char="", stream="", journal="")

    watch_settings = followuser.WatchSettings()
    watch_settings.submit = bool(form.submit)
    watch_settings.collect = bool(form.collect)
    watch_settings.char = bool(form.char)
    watch_settings.stream = bool(form.stream)
    watch_settings.journal = bool(form.journal)
    followuser.update(request.userid, define.get_int(form.userid), watch_settings)

    raise HTTPSeeOther(location="/manage/following")


@view_config(route_name="control_friends", renderer='/manage/friends.jinja2', request_method="GET")
@login_required
def manage_friends_(request):
    feature = request.params.get("feature")

    if feature == "pending":
        return {
            'query': frienduser.select_requests(request.userid),
            'title': "Pending Friend Requests",
            'feature': 'pending'
        }
    else:
        return {
            'query': frienduser.select_accepted(request.userid),
            'title': "Friends",
            'feature': 'accepted'
        }


@view_config(route_name="manage_ignore", renderer='/manage/ignore.jinja2')
@login_required
def manage_ignore_(request):
    return {'query': ignoreuser.select(request.userid), 'title': "Ignored Users"}


@view_config(route_name="control_collections", renderer='/manage/collections.jinja2', request_method="GET")
@login_required
def manage_collections_get_(request):
    form = request.web_input(feature="", backid="", nextid="")
    backid = int(form.backid) if form.backid else None
    nextid = int(form.nextid) if form.nextid else None

    rating = define.get_rating(request.userid)

    if form.feature == "pending":
        return {
            'query': collection.select_list(request.userid, rating, 30, otherid=request.userid, backid=backid,
                                            nextid=nextid, pending=True),
            'userid': request.userid, 'title': "Pending Collections",
            'feature': 'pending'
        }

    return {
        'query': collection.select_list(request.userid, rating, 30, otherid=request.userid, backid=backid,
                                        nextid=nextid),
        'title': "Accepted Collections",
        'feature': 'accepted'
    }


@view_config(route_name="control_collections", renderer='/manage/collections.jinja2', request_method="POST")
@login_required
@token_checked
def manage_collections_post_(request):
    form = request.web_input(submissions=[], action="")
    # submissions input format: "submissionID;collectorID"
    # we have to split it apart because each offer on a submission is a single checkbox
    # but needs collector's ID for unambiguity
    intermediate = [x.split(";") for x in form.submissions]
    submissions = [(int(x[0]), int(x[1])) for x in intermediate]

    if form.action == "accept":
        collection.pending_accept(request.userid, submissions)
    elif form.action == "reject":
        collection.pending_reject(request.userid, submissions)
    elif form.action == "remove":
        collection.remove(request.userid, (x[0] for x in submissions))
    else:
        raise WeasylError("Unexpected")

    raise HTTPSeeOther(location="/manage/collections?feature=pending")


@view_config(route_name="manage_thumbnail_", renderer='/manage/thumbnail.jinja2', request_method="GET")
@login_required
def manage_thumbnail_get_(request):
    form = request.web_input(submitid="", charid="")
    submitid = define.get_int(form.submitid)
    charid = define.get_int(form.charid)

    if submitid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(submitid=submitid):
        raise WeasylError("InsufficientPermissions")
    if charid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(charid=charid):
        raise WeasylError("InsufficientPermissions")
    if not submitid and not charid:
        raise WeasylError("Unexpected")

    if charid:
        source_path = define.url_make(charid, "char/.thumb", root=True)
        if os.path.exists(source_path):
            source = define.url_make(charid, "char/.thumb")
        else:
            source = define.url_make(charid, "char/cover")
    else:
        try:
            source = thumbnail.thumbnail_source(submitid)['display_url']
        except WeasylError:
            source = None

    return {
        'feature': "submit" if submitid else "char",
        'targetid': define.get_targetid(submitid, charid),
        'thumbnail': source,
        'exists': bool(source),
        'title': "Select Thumbnail",
        'options': ['imageselect']
    }


@view_config(route_name="manage_thumbnail_", renderer='/manage/thumbnail.jinja2', request_method="POST")
@login_required
@token_checked
def manage_thumbnail_post_(request):
    form = request.web_input(submitid="", charid="", x1="", y1="", x2="", y2="", thumbfile="")
    submitid = define.get_int(form.submitid)
    charid = define.get_int(form.charid)

    if submitid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(submitid=submitid):
        raise WeasylError("InsufficientPermissions")
    if charid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(charid=charid):
        raise WeasylError("InsufficientPermissions")
    if not submitid and not charid:
        raise WeasylError("Unexpected")

    if form.thumbfile:
        thumbnail.upload(form.thumbfile, submitid=submitid, charid=charid)
        if submitid:
            raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
        else:
            raise HTTPSeeOther(location="/manage/thumbnail?charid=%i" % (charid,))
    else:
        thumbnail.create(form.x1, form.y1, form.x2, form.y2, submitid=submitid, charid=charid)
        if submitid:
            raise HTTPSeeOther(location="/submission/%i" % (submitid,))
        else:
            raise HTTPSeeOther(location="/character/%i" % (charid,))


@view_config(route_name="control_tagfilters", renderer='/manage/tagfilters.jinja2', request_method="GET")
@login_required
def manage_tagfilters_get_(request):
    return {
        'blocktag': blocktag.select(request.userid),
        'filter_ratings': profile.get_user_ratings(request.userid),
        'title': "Tag Filters"
    }


@view_config(route_name="control_tagfilters", renderer='/manage/tagfilters.jinja2', request_method="POST")
@login_required
@token_checked
def manage_tagfilters_post_(request):
    form = request.web_input(do="", title="", rating="")

    if form.do == "create":
        blocktag.insert(request.userid, title=form.title, rating=define.get_int(form.rating))
    elif form.do == "remove":
        blocktag.remove(request.userid, title=form.title)

    raise HTTPSeeOther(location="/manage/tagfilters")


@view_config(route_name="control_avatar", renderer='/manage/avatar.jinja2', request_method="GET")
@login_required
def manage_avatar_get_(request):
    try:
        avatar_source = avatar.avatar_source(request.userid)
    except WeasylError:
        avatar_source_url = None
    else:
        avatar_source_url = avatar_source['display_url']

    return {
        'avatar': avatar_source_url,
        'exists': avatar_source_url is not None,
        'options': ["imageselect", "square_select"],
        'title': "Edit Avatar"
    }


@view_config(route_name="control_avatar", renderer='/manage/avatar.jinja2', request_method="POST")
@login_required
@token_checked
def manage_avatar_post_(request):
    form = request.web_input(image="", x1=0, y1=0, x2=0, y2=0)

    avatar.create(request.userid, form.x1, form.y1, form.x2, form.y2)
    raise HTTPSeeOther(location="/control")


@view_config(route_name="control_banner", renderer='/manage/banner.jinja2', request_method="GET")
@login_required
def manage_banner_get_(request):
    return {'title': "Edit Banner"}


@view_config(route_name="control_banner", renderer='/manage/banner.jinja2', request_method="POST")
@login_required
@token_checked
def manage_banner_post_(request):
    form = request.web_input(image="")

    banner.upload(request.userid, form.image)
    raise HTTPSeeOther(location="/control")


@view_config(route_name="control_alias", renderer='/manage/alias.jinja2', request_method="GET")
@login_required
def manage_alias_get_(request):
    return {'query': useralias.select(request.userid), 'title': "Edit Username Alias"}


@view_config(route_name="control_alias", renderer='/manage/alias.jinja2', request_method="POST")
@login_required
@token_checked
def manage_alias_post_(request):
    form = request.web_input(username="")

    useralias.set(request.userid, define.get_sysname(form.username))
    raise HTTPSeeOther(location="/control")


@view_config(route_name="control_sfw_toggle", request_method="POST")
@login_required
@token_checked
@disallow_api
def sfw_toggle_(request):
    form = request.web_input(redirect="/index")

    currentstate = request.cookies.get('sfwmode', "nsfw")
    newstate = "sfw" if currentstate == "nsfw" else "nsfw"
    request.set_cookie_on_response("sfwmode", newstate, 60 * 60 * 24 * 365)
    # release the index page's cache so it shows the new ratings if they visit it
    index.template_fields.invalidate(request.userid)
    raise HTTPSeeOther(location=form.redirect)

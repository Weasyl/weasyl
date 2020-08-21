from __future__ import absolute_import

import os

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

import libweasyl.ratings as ratings
from libweasyl import staff

from weasyl.controllers.decorators import disallow_api, login_required, token_checked
from weasyl.error import WeasylError
from weasyl import (
    api, avatar, banner, blocktag, collection, commishinfo,
    define, emailer, folder, followuser, frienduser, ignoreuser,
    index, login, oauth2, profile, searchtag, thumbnail, useralias, orm)


# Control panel functions
@login_required
def control_(request):
    return Response(define.webpage(request.userid, "control/control.html", [
        # Premium
        define.get_premium(request.userid),
        define.is_vouched_for(request.userid),
    ], title="Settings"))


@login_required
@token_checked
def control_uploadavatar_(request):
    image = request.params.get('image', u'')
    if image != u'':
        image = image.file.read()

    manage = avatar.upload(request.userid, image)
    if manage:
        raise HTTPSeeOther(location="/manage/avatar")
    else:
        raise HTTPSeeOther(location="/control")


@login_required
def control_editprofile_get_(request):
    userinfo = profile.select_userinfo(request.userid)
    return Response(define.webpage(request.userid, "control/edit_profile.html", [
        # Profile
        profile.select_profile(request.userid),
        # User information
        userinfo,
    ], title="Edit Profile", options=["typeahead"]))


@login_required
@token_checked
def control_editprofile_put_(request):
    site_names = request.params.getall('site_names')
    site_values = request.params.getall('site_values')
    ftrade = request.params.get('set_trade', '')
    frequest = request.params.get('set_request', '')
    fcommish = request.params.get('set_commish', '')

    if len(site_names) != len(site_values):
        raise WeasylError('Unexpected')

    sites = zip(site_names, site_values)

    if 'more' in request.params:
        profile_form = {
            'username': define.get_display_name(request.userid),
            'full_name': request.params.get('full_name', ''),
            'catchphrase': request.params.get('catchphrase', ''),
            'settings': fcommish + ftrade + frequest,
            'config': request.params.get('profile_display', ''),
            'profile_text': request.params.get('profile_text', '')
        }
        userinfo_form = {
            'show_age': request.params.get('show_age', ''),
            'gender': request.params.get('gender', ''),
            'country': request.params.get('country', ''),
            'sorted_user_links': [(name, [value]) for name, value in sites]
        }
        return Response(define.webpage(request.userid, "control/edit_profile.html", [profile_form, userinfo_form], title="Edit Profile", options=["typeahead"]))

    p = orm.Profile()
    p.full_name = request.params.get('full_name', '')
    p.catchphrase = request.params.get('catchphrase', '')
    p.profile_text = request.params.get('profile_text', '')
    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, request.params.get('set_trade', ''))
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, request.params.get('set_request', ''))
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, request.params.get('set_commish', ''))
    profile.edit_profile(request.userid, p, set_trade=set_trade,
                         set_request=set_request, set_commission=set_commission,
                         profile_display=request.params.get('profile_display', ''))

    profile.edit_userinfo(
        request.userid,
        site_names,
        site_values,
        request.params.get('gender', ''),
        request.params.get('country', ''),
        request.params.get('show_age', '')
    )

    raise HTTPSeeOther(location="/control")


@login_required
def control_editcommissionsettings_(request):
    return Response(define.webpage(request.userid, "control/edit_commissionsettings.html", [
        # Commission prices
        commishinfo.select_list(request.userid),
        commishinfo.CURRENCY_CHARMAP,
        commishinfo.PRESET_COMMISSION_CLASSES,
        profile.select_profile(request.userid)
    ], title="Edit Commission Settings"))


@login_required
@token_checked
def control_editcommishinfo_(request):
    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, request.params.get('set_trade', ''))
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, request.params.get('set_request', ''))
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, request.params.get('set_commish', ''))

    profile.edit_profile_settings(request.userid, set_trade, set_request, set_commission)
    commishinfo.edit_content(request.userid, request.params.get('content', ''))
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_createcommishclass_(request):
    title = request.params.get('title', '') or request.params.get('titlepreset', '')
    currency = request.params.get('currency', '').replace("$", "")

    classid = commishinfo.create_commission_class(request.userid, title.strip())
    # Try to create a base price for it. If we fail, try to clean up the class.
    try:
        price = orm.CommishPrice()
        price.title = request.params.get('price_title', '').strip()
        price.classid = classid
        price.amount_min = commishinfo.parse_currency(request.params.get('min_amount', ''))
        price.amount_max = commishinfo.parse_currency(request.params.get('max_amount', ''))
        commishinfo.create_price(request.userid, price, currency=currency)
    except WeasylError as we:
        commishinfo.remove_class(request.userid, classid)
        raise we
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_editcommishclass_(request):
    commishclass = orm.CommishClass()
    commishclass.title = request.params.get('title', '').strip()
    commishclass.classid = define.get_int(request.params.get('classid', ''))
    commishinfo.edit_class(request.userid, commishclass)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_removecommishclass_(request):
    classid = define.get_int(request.params.get('classid', ""))

    if not classid:
        raise WeasylError("classidInvalid")

    commishinfo.remove_class(request.userid, classid)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_createcommishprice_(request):
    currency = request.params.get('currency', '').replace("$", "")

    price = orm.CommishPrice()
    price.title = request.params.get('title', '').strip()
    price.classid = define.get_int(request.params.get('classid', ''))
    price.amount_min = commishinfo.parse_currency(request.params.get('min_amount', ''))
    price.amount_max = commishinfo.parse_currency(request.params.get('max_amount', ''))
    commishinfo.create_price(request.userid, price, currency=currency,
                             settings=request.params.get('settings', ''))
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_editcommishprice_(request):
    currency = request.params.get('currency', '').replace("$", "")

    price = orm.CommishPrice()
    price.title = request.params.get('title', '').strip()
    price.priceid = define.get_int(request.params.get('priceid', ''))
    price.amount_min = commishinfo.parse_currency(request.params.get('min_amount', ''))
    price.amount_max = commishinfo.parse_currency(request.params.get('max_amount', ''))
    edit_prices = bool(price.amount_min or price.amount_max)
    commishinfo.edit_price(request.userid, price, currency=currency,
                           settings=request.params.get('settings', ''), edit_prices=edit_prices)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
@token_checked
def control_removecommishprice_(request):
    priceid = define.get_int(request.params.get('priceid', ""))

    if not priceid:
        raise WeasylError("priceidInvalid")

    commishinfo.remove_price(request.userid, priceid)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


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

    return Response(define.webpage(
        request.userid,
        "control/username.html",
        (define.get_display_name(request.userid), existing_redirect, days if days is not None and days < 30 else None),
        title="Change Username",
    ))


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

        return Response(define.errorpage(
            request.userid,
            "Your username has been changed.",
            [["Go Back", "/control/username"], ["Return Home", "/"]],
        ))
    elif request.POST['do'] == 'release':
        login.release_username(
            define.engine,
            acting_user=request.userid,
            target_user=request.userid,
        )

        return Response(define.errorpage(
            request.userid,
            "Your old username has been released.",
            [["Go Back", "/control/username"], ["Return Home", "/"]],
        ))
    else:
        raise WeasylError("Unexpected")


@login_required
@disallow_api
def control_editemailpassword_get_(request):
    return Response(define.webpage(
        request.userid,
        "control/edit_emailpassword.html",
        [profile.select_manage(request.userid)["email"]],
        title="Edit Password and Email Address"
    ))


@login_required
@disallow_api
@token_checked
def control_editemailpassword_post_(request):
    fnewemail = request.params.get('newemail', '')
    fnewemailcheck = request.params.get('newemailcheck', '')

    newemail = emailer.normalize_address(fnewemail)
    newemailcheck = emailer.normalize_address(fnewemailcheck)

    # Check if the email was invalid; Both fields must be valid (not None), and have the form fields set
    if not newemail and not newemailcheck and fnewemail != "" and fnewemailcheck != "":
        raise WeasylError("emailInvalid")

    return_message = profile.edit_email_password(
        request.userid, request.params.get('username', ''), request.params.get('password', ''), newemail, newemailcheck,
        request.params.get('newpassword', ''), request.params.get('newpasscheck', '')
    )

    if not return_message:  # No changes were made
        message = "No changes were made to your account."
    else:  # Changes were made, so inform the user of this
        message = "**Success!** " + return_message
    # Finally return the message about what (if anything) changed to the user
    return Response(define.errorpage(
        request.userid, message,
        [["Go Back", "/control"], ["Return Home", "/"]])
    )


@login_required
def control_editpreferences_get_(request):
    config = define.get_config(request.userid)
    current_rating, current_sfw_rating = define.get_config_rating(request.userid)
    age = profile.get_user_age(request.userid)
    allowed_ratings = ratings.get_ratings_for_age(age)
    jsonb_settings = define.get_profile_settings(request.userid)
    return Response(define.webpage(request.userid, "control/edit_preferences.html", [
        # Config
        config,
        jsonb_settings,
        # Rating
        current_rating,
        current_sfw_rating,
        age,
        allowed_ratings,
        request.weasyl_session.timezone.timezone,
        define.timezones(),
    ], title="Site Preferences"))


@login_required
@token_checked
def control_editpreferences_post_(request):
    rating = ratings.CODE_MAP[define.get_int(request.params.get('rating', ''))]
    jsonb_settings = define.get_profile_settings(request.userid)
    jsonb_settings.disable_custom_thumbs = request.params.get('custom_thumbs', '') == "disable"
    jsonb_settings.max_sfw_rating = define.get_int(request.params.get('sfwrating', ''))

    preferences = profile.Config()
    preferences.twelvehour = bool(request.params.get('twelvehour', ''))
    preferences.rating = rating
    preferences.tagging = bool(request.params.get('tagging', ''))
    preferences.hideprofile = bool(request.params.get('hideprofile', ''))
    preferences.hidestats = bool(request.params.get('hidestats', ''))
    preferences.hidefavorites = bool(request.params.get('hidefavorites', ''))
    preferences.hidefavbar = bool(request.params.get('hidefavbar', ''))
    shouts = request.params.get('shouts', '')
    preferences.shouts = ("friends_only" if shouts == "x" else
                          "staff_only" if shouts == "w" else "anyone")
    notes = request.params.get('notes', '')
    preferences.notes = ("friends_only" if notes == "z" else
                         "staff_only" if notes == "y" else "anyone")
    preferences.filter = bool(request.params.get('filter', ''))
    preferences.follow_s = bool(request.params.get('follow_s', ''))
    preferences.follow_c = bool(request.params.get('follow_c', ''))
    preferences.follow_f = bool(request.params.get('follow_f', ''))
    preferences.follow_t = bool(request.params.get('follow_t', ''))
    preferences.follow_j = bool(request.params.get('follow_j', ''))

    profile.edit_preferences(request.userid, timezone=request.params.get('timezone', ''),
                             preferences=preferences, jsonb_settings=jsonb_settings)
    # release the cache on the index page in case the Maximum Viewable Content Rating changed.
    index.template_fields.invalidate(request.userid)
    raise HTTPSeeOther(location="/control")


@login_required
@token_checked
def control_createfolder_(request):
    folder.create(request.userid, request.params.get('title', ''), request.params.get('parentid', ''))
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_renamefolder_(request):
    folderid = request.params.get('folderid', '')
    title = request.params.get('title', '')

    if define.get_int(folderid):
        folder.rename(request.userid, title, folderid)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_removefolder_(request):
    folderid = define.get_int(request.params.get('folderid', ''))

    if folderid:
        folder.remove(request.userid, folderid)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
def control_editfolder_get_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "manage/folder_options.html", [
        folder.select_info(folderid),
    ], title="Edit Folder Options"))


@login_required
@token_checked
def control_editfolder_post_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        raise WeasylError('InsufficientPermissions')

    settings = request.params.getall('settings')
    folder.update_settings(folderid, settings)
    raise HTTPSeeOther(location='/manage/folders')


@login_required
@token_checked
def control_movefolder_(request):
    folderid = define.get_int(request.params.get('folderid', ''))
    parentid = define.get_int(request.params.get('parentid', ''))

    if folderid and parentid >= 0:
        folder.move(request.userid, folderid, parentid)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_ignoreuser_(request):
    ignoreuser.insert(request.userid, define.get_userid_list(request.params.get('username', '')))
    raise HTTPSeeOther(location="/manage/ignore")


@login_required
@token_checked
def control_unignoreuser_(request):
    ignoreuser.remove(request.userid, define.get_userid_list(request.params.get('username', '')))
    raise HTTPSeeOther(location="/manage/ignore")


@login_required
def control_streaming_get_(request):
    target = request.params.get('target', '')
    if target and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')
    elif target:
        target = define.get_int(target)
    else:
        target = request.userid

    return Response(define.webpage(request.userid, "control/edit_streaming.html", [
        # Profile
        profile.select_profile(target),
        target,
    ], title="Edit Streaming Settings"))


@login_required
@token_checked
def control_streaming_post_(request):
    target = request.params.get('target', '')

    if target and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')

    if target:
        target = int(target)
    else:
        target = request.userid

    stream_length = define.clamp(define.get_int(request.params.get('stream_length', '')), 0, 360)
    p = orm.Profile()
    p.stream_text = request.params.get('stream_text', '')
    p.stream_url = define.text_fix_url(request.params.get('stream_url', '').strip())
    set_stream = request.params.get('set_stream', '')

    profile.edit_streaming_settings(request.userid, target, p,
                                    set_stream=set_stream,
                                    stream_length=stream_length)

    if target:
        target_username = define.get_sysname(define.get_display_name(target))
        raise HTTPSeeOther(location="/modcontrol/manageuser?name=" + target_username)
    else:
        raise HTTPSeeOther(location="/control")


@login_required
@disallow_api
def control_apikeys_get_(request):
    return Response(define.webpage(request.userid, "control/edit_apikeys.html", [
        api.get_api_keys(request.userid),
        oauth2.get_consumers_for_user(request.userid),
    ], title="API Keys"))


@login_required
@disallow_api
@token_checked
def control_apikeys_post_(request):
    if request.params.get('add-api-key'):
        api.add_api_key(request.userid, request.params.get('add-key-description'))
    if request.params.get('delete-api-keys'):
        api.delete_api_keys(request.userid, request.params.getall('delete-api-keys'))
    if request.params.get('revoke-oauth2-consumers'):
        oauth2.revoke_consumers_for_user(request.userid, request.params.getall('revoke-oauth2-consumers'))

    raise HTTPSeeOther(location="/control/apikeys")


@login_required
def control_tagrestrictions_get_(request):
    return Response(define.webpage(request.userid, "control/edit_tagrestrictions.html", (
        sorted(searchtag.query_user_restricted_tags(request.userid)),
    ), title="Edit Community Tagging Restrictions"))


@login_required
@token_checked
def control_tagrestrictions_post_(request):
    tags = searchtag.parse_restricted_tags(request.params["tags"])
    searchtag.edit_user_tag_restrictions(request.userid, tags)

    raise HTTPSeeOther(location=request.route_path('control_tagrestrictions'))


@login_required
def manage_folders_(request):
    return Response(define.webpage(request.userid, "manage/folders.html", [
        # Folders dropdown
        folder.select_flat(request.userid),
    ], title="Submission Folders"))


@login_required
def manage_following_get_(request):
    userid = define.get_int(request.params.get('userid', ''))
    backid = define.get_int(request.params.get('backid', ''))
    nextid = define.get_int(request.params.get('nextid', ''))

    if userid:
        return Response(define.webpage(request.userid, "manage/following_user.html", [
            # Profile
            profile.select_profile(userid),
            # Follow settings
            followuser.select_settings(request.userid, userid),
        ], title="Followed User"))
    else:
        return Response(define.webpage(request.userid, "manage/following_list.html", [
            # Following
            followuser.manage_following(request.userid, 44, backid=backid, nextid=nextid),
        ], title="Users You Follow"))


@login_required
@token_checked
def manage_following_post_(request):
    watch_settings = followuser.WatchSettings()
    watch_settings.submit = bool(request.params.get('submit', ''))
    watch_settings.collect = bool(request.params.get('collect', ''))
    watch_settings.char = bool(request.params.get('char', ''))
    watch_settings.stream = bool(request.params.get('stream', ''))
    watch_settings.journal = bool(request.params.get('journal', ''))
    followuser.update(request.userid, define.get_int(request.params.get('userid', '')), watch_settings)

    raise HTTPSeeOther(location="/manage/following")


@login_required
def manage_friends_(request):
    feature = request.params.get("feature")

    if feature == "pending":
        return Response(define.webpage(request.userid, "manage/friends_pending.html", [
            frienduser.select_requests(request.userid),
        ], title="Pending Friend Requests"))
    else:
        return Response(define.webpage(request.userid, "manage/friends_accepted.html", [
            frienduser.select_accepted(request.userid),
        ], title="Friends"))


@login_required
def manage_ignore_(request):
    return Response(define.webpage(request.userid, "manage/ignore.html", [
        ignoreuser.select(request.userid),
    ], title="Ignored Users"))


@login_required
def manage_collections_get_(request):
    backid = int(request.params.get('backid', '')) if request.params.get('backid', False) else None
    nextid = int(request.params.get('nextid', '')) if request.params.get('nextid', False) else None

    rating = define.get_rating(request.userid)

    if request.params.get('feature', '') == "pending":
        return Response(define.webpage(request.userid, "manage/collections_pending.html", [
            # Pending Collections
            collection.select_list(request.userid, rating, 30, otherid=request.userid, backid=backid, nextid=nextid,
                                   pending=True),
            request.userid
        ], title="Pending Collections"))

    return Response(define.webpage(request.userid, "manage/collections_accepted.html", [
        # Accepted Collections
        collection.select_list(request.userid, rating, 30, otherid=request.userid, backid=backid, nextid=nextid),
    ], title="Accepted Collections"))


@login_required
@token_checked
def manage_collections_post_(request):
    # submissions input format: "submissionID;collectorID"
    # we have to split it apart because each offer on a submission is a single checkbox
    # but needs collector's ID for unambiguity
    intermediate = [x.split(";") for x in request.params.getall('submissions')]
    submissions = [(int(x[0]), int(x[1])) for x in intermediate]

    action = request.params.get('action', '')

    if action == "accept":
        collection.pending_accept(request.userid, submissions)
    elif action == "reject":
        collection.pending_reject(request.userid, submissions)
    else:
        raise WeasylError("Unexpected")

    raise HTTPSeeOther(location="/manage/collections?feature=pending")


@login_required
def manage_thumbnail_get_(request):
    submitid = define.get_int(request.params.get('submitid', ''))
    charid = define.get_int(request.params.get('charid', ''))

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

    return Response(define.webpage(request.userid, "manage/thumbnail.html", [
        # Feature
        "submit" if submitid else "char",
        # Targetid
        define.get_targetid(submitid, charid),
        # Thumbnail
        source,
        # Exists
        bool(source),
    ], options=['imageselect'], title="Select Thumbnail"))


@login_required
@token_checked
def manage_thumbnail_post_(request):
    submitid = define.get_int(request.params.get('submitid', ''))
    charid = define.get_int(request.params.get('charid', ''))

    if submitid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(submitid=submitid):
        raise WeasylError("InsufficientPermissions")
    if charid and request.userid not in staff.ADMINS and request.userid != define.get_ownerid(charid=charid):
        raise WeasylError("InsufficientPermissions")
    if not submitid and not charid:
        raise WeasylError("Unexpected")

    thumbfile = request.params.get('thumbfile', u'')
    if thumbfile != u'':
        thumbfile = thumbfile.file.read()
    else:
        thumbfile = None

    if thumbfile:
        thumbnail.upload(thumbfile, submitid=submitid, charid=charid)
        if submitid:
            raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
        else:
            raise HTTPSeeOther(location="/manage/thumbnail?charid=%i" % (charid,))
    else:
        x1 = request.params.get('x1', '')
        y1 = request.params.get('y1', '')
        x2 = request.params.get('x2', '')
        y2 = request.params.get('y2', '')
        thumbnail.create(x1, y1, x2, y2, submitid=submitid, charid=charid)
        if submitid:
            raise HTTPSeeOther(location="/submission/%i" % (submitid,))
        else:
            raise HTTPSeeOther(location="/character/%i" % (charid,))


@login_required
def manage_tagfilters_get_(request):
    return Response(define.webpage(request.userid, "manage/tagfilters.html", [
        # Blocked tags
        blocktag.select(request.userid),
        # filterable ratings
        profile.get_user_ratings(request.userid),
    ], title="Tag Filters"))


@login_required
@token_checked
def manage_tagfilters_post_(request):
    do = request.params.get('do', '')
    title = request.params.get('title', '')

    if do == "create":
        blocktag.insert(request.userid, title=title, rating=define.get_int(request.params.get('rating', '')))
    elif do == "remove":
        blocktag.remove(request.userid, title=title)

    raise HTTPSeeOther(location="/manage/tagfilters")


@login_required
def manage_avatar_get_(request):
    try:
        avatar_source = avatar.avatar_source(request.userid)
    except WeasylError:
        avatar_source_url = None
    else:
        avatar_source_url = avatar_source['display_url']

    return Response(define.webpage(
        request.userid,
        "manage/avatar.html",
        [
            # Avatar selection
            avatar_source_url,
            # Avatar selection exists
            avatar_source_url is not None,
        ],
        options=["imageselect", "square_select"],
        title="Edit Avatar"
    ))


@login_required
@token_checked
def manage_avatar_post_(request):
    x1 = request.params.get('x1', '')
    y1 = request.params.get('y1', '')
    x2 = request.params.get('x2', '')
    y2 = request.params.get('y2', '')
    avatar.create(request.userid, x1, y1, x2, y2)
    raise HTTPSeeOther(location="/control")


@login_required
def manage_banner_get_(request):
    return Response(define.webpage(request.userid, "manage/banner.html", title="Edit Banner"))


@login_required
@token_checked
def manage_banner_post_(request):
    image = request.params.get('image', u'')
    if image != u'':
        image = image.file.read()

    banner.upload(request.userid, image)
    raise HTTPSeeOther(location="/control")


@login_required
def manage_alias_get_(request):
    return Response(define.webpage(request.userid, "manage/alias.html", [
        # Alias
        useralias.select(request.userid),
    ], title="Edit Username Alias"))


@login_required
@token_checked
def manage_alias_post_(request):
    useralias.set(request.userid, define.get_sysname(request.params.get('username', '')))
    raise HTTPSeeOther(location="/control")


@login_required
@token_checked
@disallow_api
def sfw_toggle_(request):
    redirect = request.params.get('redirect', '/index')

    currentstate = request.cookies.get('sfwmode', "nsfw")
    newstate = "sfw" if currentstate == "nsfw" else "nsfw"
    request.set_cookie_on_response("sfwmode", newstate, 60 * 60 * 24 * 365)
    # release the index page's cache so it shows the new ratings if they visit it
    index.template_fields.invalidate(request.userid)
    raise HTTPSeeOther(location=redirect)

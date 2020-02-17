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
    define, emailer, errorcode, folder, followuser, frienduser, ignoreuser,
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
    form = request.web_input(image="")

    manage = avatar.upload(request.userid, form.image)
    if manage:
        raise HTTPSeeOther(location="/manage/avatar")
    else:
        raise HTTPSeeOther(location="/control")


@login_required
def control_editprofile_get_(request):
    userinfo = profile.select_userinfo(request.userid)
    return Response(define.webpage(request.userid, "control/edit_profile.html", [
        # Profile
        profile.select_profile(request.userid, commish=False),
        # User information
        userinfo,
    ], title="Edit Profile", options=["typeahead"]))


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
        form.username = define.get_display_name(request.userid)
        form.sorted_user_links = [(name, [value]) for name, value in zip(form.site_names, form.site_values)]
        form.settings = form.set_commish + form.set_trade + form.set_request
        form.config = form.profile_display
        return Response(define.webpage(request.userid, "control/edit_profile.html", [form, form], title="Edit Profile", options=["typeahead"]))

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
    form = request.web_input(content="", set_commish="", set_trade="", set_request="")
    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, form.set_trade)
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, form.set_request)
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, form.set_commish)

    profile.edit_profile_settings(request.userid, set_trade, set_request, set_commission)
    commishinfo.edit_content(request.userid, form.content)
    raise HTTPSeeOther(location="/control/editcommissionsettings")


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


@login_required
@token_checked
def control_editcommishclass_(request):
    form = request.web_input(classid="", title="")

    commishclass = orm.CommishClass()
    commishclass.title = form.title.strip()
    commishclass.classid = define.get_int(form.classid)
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


@login_required
@token_checked
def control_createfolder_(request):
    form = request.web_input(title="", parentid="")

    folder.create(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_renamefolder_(request):
    form = request.web_input(folderid="", title="")

    if define.get_int(form.folderid):
        folder.rename(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_removefolder_(request):
    form = request.web_input(folderid="")
    form.folderid = define.get_int(form.folderid)

    if form.folderid:
        folder.remove(request.userid, form.folderid)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
def control_editfolder_get_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "manage/folder_options.html", [
        folder.select_info(folderid),
    ], title="Edit Folder Options"))


@login_required
@token_checked
def control_editfolder_post_(request):
    folderid = int(request.matchdict['folderid'])
    if not folder.check(request.userid, folderid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    form = request.web_input(settings=[])
    folder.update_settings(folderid, form.settings)
    raise HTTPSeeOther(location='/manage/folders')


@login_required
@token_checked
def control_movefolder_(request):
    form = request.web_input(folderid="", parentid="")
    form.folderid = define.get_int(form.folderid)

    if form.folderid and define.get_int(form.parentid) >= 0:
        folder.move(request.userid, form)
    raise HTTPSeeOther(location="/manage/folders")


@login_required
@token_checked
def control_ignoreuser_(request):
    form = request.web_input(username="")

    ignoreuser.insert(request.userid, define.get_userid_list(form.username))
    raise HTTPSeeOther(location="/manage/ignore")


@login_required
@token_checked
def control_unignoreuser_(request):
    form = request.web_input(username="")

    ignoreuser.remove(request.userid, define.get_userid_list(form.username))
    raise HTTPSeeOther(location="/manage/ignore")


@login_required
def control_streaming_get_(request):
    form = request.web_input(target='')
    if form.target and request.userid not in staff.MODS:
        return Response(define.errorpage(request.userid, errorcode.permission))
    elif form.target:
        target = define.get_int(form.target)
    else:
        target = request.userid

    return Response(define.webpage(request.userid, "control/edit_streaming.html", [
        # Profile
        profile.select_profile(target, commish=False),
        form.target,
    ], title="Edit Streaming Settings"))


@login_required
@token_checked
def control_streaming_post_(request):
    form = request.web_input(target="", set_stream="", stream_length="", stream_url="", stream_text="")

    if form.target and request.userid not in staff.MODS:
        return Response(define.errorpage(request.userid, errorcode.permission))

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
    form = request.web_input(**{'delete-api-keys': [], 'revoke-oauth2-consumers': []})

    if form.get('add-api-key'):
        api.add_api_key(request.userid, form.get('add-key-description'))
    if form.get('delete-api-keys'):
        api.delete_api_keys(request.userid, form['delete-api-keys'])
    if form.get('revoke-oauth2-consumers'):
        oauth2.revoke_consumers_for_user(request.userid, form['revoke-oauth2-consumers'])

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
        folder.select_list(request.userid, "drop/all"),
    ], title="Submission Folders"))


@login_required
def manage_following_get_(request):
    form = request.web_input(userid="", backid="", nextid="")
    form.userid = define.get_int(form.userid)
    form.backid = define.get_int(form.backid)
    form.nextid = define.get_int(form.nextid)

    if form.userid:
        return Response(define.webpage(request.userid, "manage/following_user.html", [
            # Profile
            profile.select_profile(form.userid, avatar=True),
            # Follow settings
            followuser.select_settings(request.userid, form.userid),
        ], title="Followed User"))
    else:
        return Response(define.webpage(request.userid, "manage/following_list.html", [
            # Following
            followuser.manage_following(request.userid, 44, backid=form.backid, nextid=form.nextid),
        ], title="Users You Follow"))


@login_required
@token_checked
def manage_following_post_(request):
    form = request.web_input(userid="", submit="", collect="", char="", stream="", journal="")

    watch_settings = followuser.WatchSettings()
    watch_settings.submit = bool(form.submit)
    watch_settings.collect = bool(form.collect)
    watch_settings.char = bool(form.char)
    watch_settings.stream = bool(form.stream)
    watch_settings.journal = bool(form.journal)
    followuser.update(request.userid, define.get_int(form.userid), watch_settings)

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
    form = request.web_input(feature="", backid="", nextid="")
    backid = int(form.backid) if form.backid else None
    nextid = int(form.nextid) if form.nextid else None

    rating = define.get_rating(request.userid)

    if form.feature == "pending":
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
    else:
        raise WeasylError("Unexpected")

    raise HTTPSeeOther(location="/manage/collections?feature=pending")


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
    form = request.web_input(do="", title="", rating="")

    if form.do == "create":
        blocktag.insert(request.userid, title=form.title, rating=define.get_int(form.rating))
    elif form.do == "remove":
        blocktag.remove(request.userid, title=form.title)

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
    form = request.web_input(image="", x1=0, y1=0, x2=0, y2=0)

    avatar.create(request.userid, form.x1, form.y1, form.x2, form.y2)
    raise HTTPSeeOther(location="/control")


@login_required
def manage_banner_get_(request):
    return Response(define.webpage(request.userid, "manage/banner.html", title="Edit Banner"))


@login_required
@token_checked
def manage_banner_post_(request):
    form = request.web_input(image="")

    banner.upload(request.userid, form.image)
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
    form = request.web_input(username="")

    useralias.set(request.userid, define.get_sysname(form.username))
    raise HTTPSeeOther(location="/control")


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

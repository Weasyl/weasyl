import os

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

import libweasyl.ratings as ratings
from libweasyl import staff

from weasyl.controllers.decorators import disallow_api, login_required, token_checked
from weasyl.error import WeasylError
from weasyl.users import Username
from weasyl import (
    api, avatar, banner, blocktag, collection, commishinfo,
    define, emailer, folder, followuser, frienduser, ignoreuser,
    login, profile, searchtag, thumbnail, useralias, orm)


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
    query = profile.select_profile(request.userid)
    userinfo = profile.select_userinfo(request.userid, config=query["config"])
    return Response(define.webpage(request.userid, "control/edit_profile.html", [
        # Profile
        query,
        # User information
        userinfo,
    ], title="Edit Profile"))


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

    set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, form.set_trade)
    set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, form.set_request)
    set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, form.set_commish)
    profile.edit_profile_settings(
        request.userid,
        set_trade=set_trade,
        set_request=set_request,
        set_commission=set_commission,
    )

    profile.edit_profile(
        request.userid,
        full_name=form.full_name,
        catchphrase=form.catchphrase,
        profile_text=form.profile_text,
        profile_display=form.profile_display,
    )

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

    profile.edit_profile_settings(
        request.userid,
        set_trade=set_trade,
        set_request=set_request,
        set_commission=set_commission,
    )
    commishinfo.edit_content(request.userid, form.content)

    if "preferred-tags" in request.POST:
        preferred_tags = searchtag.parse_tags(request.POST["preferred-tags"])
        optout_tags = searchtag.parse_tags(request.POST["optout-tags"])
        searchtag.set_commission_preferred_tags(
            userid=request.userid,
            tag_names=preferred_tags,
        )
        searchtag.set_commission_optout_tags(
            userid=request.userid,
            tag_names=optout_tags,
        )

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
        " AND NOT cosmetic"
        " ORDER BY historyid DESC LIMIT 1",
        user=request.userid,
    ).first()

    if latest_change is None:
        existing_redirect = None
        days = None
    else:
        existing_redirect = Username.from_stored(latest_change.username) if latest_change.active else None
        days = latest_change.seconds // (3600 * 24)

    return Response(define.webpage(
        request.userid,
        "control/username.html",
        (define.get_username(request.userid), existing_redirect, days if days is not None and days < 30 else None),
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
        ))
    else:
        raise WeasylError("Unexpected")


@login_required
@disallow_api
def control_editemailpassword_get_(request):
    profile_info = profile.select_manage(request.userid)

    return Response(define.webpage(
        request.userid,
        "control/edit_emailpassword.html",
        (profile_info["email"], profile_info["username"]),
        options=("signup",),
        title="Edit Password and Email Address"
    ))


@login_required
@disallow_api
@token_checked
def control_editemailpassword_post_(request):
    newemail = emailer.normalize_address(request.POST["newemail"])

    if not newemail and request.POST["newemail"] != "":
        raise WeasylError("emailInvalid")

    return_message = profile.edit_email_password(
        userid=request.userid,
        password=request.POST["password"],
        newemail=newemail,
        newpassword=request.POST["newpassword"],
    )

    if not return_message:  # No changes were made
        message = "No changes were made to your account."
    else:  # Changes were made, so inform the user of this
        message = "**Success!** " + return_message
    # Finally return the message about what (if anything) changed to the user
    return Response(define.errorpage(request.userid, message))


@login_required
def control_editpreferences_get_(request):
    config = define.get_config(request.userid)
    current_rating = define.get_config_rating(request.userid)
    age = profile.get_user_age(request.userid)
    allowed_ratings = ratings.get_ratings_for_age(age)
    jsonb_settings = define.get_profile_settings(request.userid)
    return Response(define.webpage(request.userid, "control/edit_preferences.html", [
        # Config
        config,
        jsonb_settings,
        # Rating
        current_rating,
        allowed_ratings,
    ], title="Site Preferences"))


@login_required
@token_checked
def control_editpreferences_post_(request):
    form = request.web_input(
        rating="", sfwrating="", custom_thumbs="", tagging="",
        hideprofile="", hidestats="", hidefavorites="", hidefavbar="",
        shouts="", notes="", filter="",
        follow_s="", follow_c="", follow_f="", follow_t="",
        follow_j="")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating), ratings.GENERAL)

    preferences = profile.Config()
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

    profile.edit_preferences(request.userid,
                             preferences=preferences,
                             disable_custom_thumbs=form.custom_thumbs == "disable")
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

    folder.update_settings(folderid, request.POST.getall('settings'))
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
        raise WeasylError('InsufficientPermissions')
    elif form.target:
        target = define.get_int(form.target)
    else:
        target = request.userid

    return Response(define.webpage(request.userid, "control/edit_streaming.html", [
        # Profile
        profile.select_profile(target),
        form.target,
    ], title="Edit Streaming Settings"))


@login_required
@token_checked
def control_streaming_post_(request):
    form = request.web_input(target="", set_stream="", stream_length="", stream_url="", stream_text="")

    if form.target and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')

    if form.target:
        target = int(form.target)
    else:
        target = request.userid

    stream_length = define.clamp(define.get_int(form.stream_length), 0, 360)

    profile.edit_streaming_settings(
        request.userid,
        target,
        stream_text=form.stream_text,
        stream_url=form.stream_url,
        set_stream=form.set_stream,
        stream_length=stream_length,
    )

    if form.target:
        target_username = define.get_username(target)
        raise HTTPSeeOther(location="/modcontrol/manageuser?name=" + target_username.sysname)
    else:
        raise HTTPSeeOther(location="/control")


@login_required
@disallow_api
def control_apikeys_get_(request):
    return Response(define.webpage(request.userid, "control/edit_apikeys.html", [
        api.get_api_keys(request.userid),
    ], title="API Keys"))


@login_required
@disallow_api
@token_checked
def control_apikeys_post_(request):
    if 'add-api-key' in request.POST:
        api.add_api_key(request.userid, request.POST.getone('add-key-description'))
    if 'delete-api-keys' in request.POST:
        api.delete_api_keys(request.userid, request.POST.getall('delete-api-keys'))

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
    form = request.web_input(userid="", backid="", nextid="")
    form.userid = define.get_int(form.userid)
    form.backid = define.get_int(form.backid)
    form.nextid = define.get_int(form.nextid)

    if form.userid:
        return Response(define.webpage(request.userid, "manage/following_user.html", [
            # Profile
            profile.select_profile(form.userid),
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
            frienduser.select_friends(request.userid, request.userid),
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
    action = request.POST["action"]

    # submissions input format: "submissionID;collectorID"
    # we have to split it apart because each offer on a submission is a single checkbox
    # but needs collector's ID for unambiguity
    intermediate = [x.split(";") for x in request.POST.getall("submissions")]
    submissions = [(int(x[0]), int(x[1])) for x in intermediate]

    if action == "accept":
        collection.pending_accept(request.userid, submissions)
    elif action == "reject":
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
    ], options=('imageselect',), title="Select Thumbnail"))


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
    ], title="Blocked Tags"))


@login_required
@token_checked
def manage_tagfilters_post_(request):
    do = request.POST["do"]

    if do == "create":
        tags = request.POST.getone("title")
        blocktag.insert(request.userid, tags=tags, rating=define.get_int(request.POST["rating"]))
    elif do == "remove":
        tags = request.POST.getall("title")
        blocktag.remove_list(request.userid, tags)
    else:
        raise WeasylError("Unexpected")  # pragma: no cover

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
        options=("imageselect", "square_select"),
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

    useralias.set(request.userid, Username.create(form.username).sysname)
    raise HTTPSeeOther(location="/control")


@login_required
@token_checked
@disallow_api
def sfw_toggle_(request):
    redirect = request.POST.get("redirect", "/")

    currentstate = request.cookies.get('sfwmode', "nsfw")
    newstate = "sfw" if currentstate == "nsfw" else "nsfw"
    response = HTTPSeeOther(location=define.path_redirect(redirect))
    response.set_cookie("sfwmode", newstate, max_age=60 * 60 * 24 * 365)
    return response

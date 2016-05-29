import os

import web

import libweasyl.ratings as ratings
from libweasyl import staff

from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import (
    api, avatar, banner, blocktag, collection, commishinfo,
    define, emailer, errorcode, folder, followuser, frienduser, ignoreuser,
    index, oauth2, profile, thumbnail, useralias, orm)


# Control panel functions
class control_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "control/control.html", [
            # Premium
            define.get_premium(self.user_id),
        ])


class control_uploadavatar_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(image="")

        manage = avatar.upload(self.user_id, form.image)
        if manage:
            raise web.seeother("/manage/avatar")
        else:
            raise web.seeother("/control")


class control_editprofile_(controller_base):
    login_required = True

    def GET(self):
        userinfo = profile.select_userinfo(self.user_id)
        userinfo['sorted_user_links'] = sorted(userinfo['user_links'].items(), key=lambda kv: kv[0].lower())
        return define.webpage(self.user_id, "control/edit_profile.html", [
            # Profile
            profile.select_profile(self.user_id, commish=False),
            # User information
            userinfo,
        ])

    @define.token_checked
    def POST(self):
        form = web.input(
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
            return define.webpage(self.user_id, "control/edit_profile.html", [form, form])

        p = orm.Profile()
        p.full_name = form.full_name
        p.catchphrase = form.catchphrase
        p.profile_text = form.profile_text
        set_trade = profile.get_exchange_setting(profile.EXCHANGE_TYPE_TRADE, form.set_trade)
        set_request = profile.get_exchange_setting(profile.EXCHANGE_TYPE_REQUEST, form.set_request)
        set_commission = profile.get_exchange_setting(profile.EXCHANGE_TYPE_COMMISSION, form.set_commish)
        profile.edit_profile(self.user_id, p, set_trade=set_trade,
                             set_request=set_request, set_commission=set_commission,
                             profile_display=form.profile_display)

        profile.edit_userinfo(self.user_id, form)

        raise web.seeother("/control")


class control_editcommissionprices_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "control/edit_commissionprices.html", [
            # Commission prices
            commishinfo.select_list(self.user_id),
        ])


class control_editcommishtext_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(content="")

        commishinfo.edit_content(self.user_id, form.content)
        raise web.seeother("/control/editcommissionprices")


class control_createcommishclass_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(title="")

        commishinfo.create_commission_class(self.user_id, form.title.strip())
        raise web.seeother("/control/editcommissionprices")


class control_editcommishclass_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(classid="")

        commishclass = orm.CommishClass()
        commishclass.title = form.title.strip()
        commishclass.classid = define.get_int(form.classid)
        commishinfo.edit_class(self.user_id, commishclass)
        raise web.seeother("/control/editcommissionprices")


class control_removecommishclass_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(classid="")

        commishinfo.remove_class(self.user_id, form.classid)
        raise web.seeother("/control/editcommissionprices")


class control_createcommishprice_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(title="", classid="", min_amount="", max_amount="", currency="", settings="")

        price = orm.CommishPrice()
        price.title = form.title.strip()
        price.classid = define.get_int(form.classid)
        price.amount_min = commishinfo.convert_currency(form.min_amount)
        price.amount_max = commishinfo.convert_currency(form.max_amount)
        commishinfo.create_price(self.user_id, price, currency=form.currency,
                                 settings=form.settings)
        raise web.seeother("/control/editcommissionprices")


class control_editcommishprice_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(priceid="", title="", min_amount="", max_amount="", edit_settings="", currency="", settings="")

        price = orm.CommishPrice()
        price.title = form.title.strip()
        price.priceid = define.get_int(form.priceid)
        price.amount_min = commishinfo.convert_currency(form.min_amount)
        price.amount_max = commishinfo.convert_currency(form.max_amount)
        edit_prices = bool(price.amount_min or price.amount_max)
        commishinfo.edit_price(self.user_id, price, currency=form.currency,
                               settings=form.settings, edit_prices=edit_prices, edit_settings=form.edit_settings)
        raise web.seeother("/control/editcommissionprices")


class control_removecommishprice_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(classid="")

        commishinfo.remove_price(self.user_id, form.priceid)
        raise web.seeother("/control/editcommissionprices")


class control_editemailpassword_(controller_base):
    login_required = True
    disallow_api = True

    def GET(self):
        return define.webpage(self.user_id, "control/edit_emailpassword.html",
                              [profile.select_manage(self.user_id)["email"]])

    @define.token_checked
    def POST(self):
        form = web.input(newemail="", newemailcheck="", newpassword="", newpasscheck="", password="")

        newemail = emailer.normalize_address(form.newemail)
        newemailcheck = emailer.normalize_address(form.newemailcheck)

        profile.edit_email_password(self.user_id, form.username, form.password,
                                    newemail, newemailcheck, form.newpassword, form.newpasscheck)

        return define.errorpage(
            self.user_id, "**Success!** Your settings have been updated.",
            [["Go Back", "/control"], ["Return Home", "/"]])


class control_editpreferences_(controller_base):
    login_required = True

    def GET(self):
        config = define.get_config(self.user_id)
        current_rating, current_sfw_rating = define.get_config_rating(self.user_id)
        age = profile.get_user_age(self.user_id)
        allowed_ratings = ratings.get_ratings_for_age(age)
        jsonb_settings = define.get_profile_settings(self.user_id)
        return define.webpage(self.user_id, "control/edit_preferences.html", [
            # Config
            config,
            jsonb_settings,
            # Rating
            current_rating,
            current_sfw_rating,
            age,
            allowed_ratings,
            web.ctx.weasyl_session.timezone.timezone,
            define.timezones(),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(
            rating="", sfwrating="", custom_thumbs="", tagging="", edittagging="",
            hideprofile="", hidestats="", hidefavorites="", hidefavbar="",
            shouts="", notes="", filter="",
            follow_s="", follow_c="", follow_f="", follow_t="",
            follow_j="", timezone="", twelvehour="")

        rating = ratings.CODE_MAP[define.get_int(form.rating)]
        jsonb_settings = define.get_profile_settings(self.user_id)
        jsonb_settings.disable_custom_thumbs = form.custom_thumbs == "disable"
        jsonb_settings.max_sfw_rating = define.get_int(form.sfwrating)

        preferences = profile.Config()
        preferences.twelvehour = bool(form.twelvehour)
        preferences.rating = rating
        preferences.tagging = bool(form.tagging)
        preferences.edittagging = bool(form.edittagging)
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

        profile.edit_preferences(self.user_id, timezone=form.timezone,
                                 preferences=preferences, jsonb_settings=jsonb_settings)
        # release the cache on the index page in case the Maximum Viewable Content Rating changed.
        index.template_fields.invalidate(self.user_id)
        raise web.seeother("/control")


class control_createfolder_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(title="", parentid="")

        folder.create(self.user_id, form)
        raise web.seeother("/manage/folders")


class control_renamefolder_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(folderid="", title="")

        if define.get_int(form.folderid):
            folder.rename(self.user_id, form)
        raise web.seeother("/manage/folders")


class control_removefolder_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(folderid="")
        form.folderid = define.get_int(form.folderid)

        if form.folderid:
            folder.remove(self.user_id, form.folderid)
        raise web.seeother("/manage/folders")


class control_editfolder_(controller_base):
    login_required = True

    def GET(self, folderid):
        folderid = int(folderid)
        if not folder.check(self.user_id, folderid):
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "manage/folder_options.html", [
            folder.select_info(folderid),
        ])

    @define.token_checked
    def POST(self, folderid):
        folderid = int(folderid)
        if not folder.check(self.user_id, folderid):
            return define.errorpage(self.user_id, errorcode.permission)

        form = web.input(settings=[])
        folder.update_settings(folderid, form.settings)
        raise web.seeother('/manage/folders')


class control_movefolder_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(folderid="", parentid="")
        form.folderid = define.get_int(form.folderid)

        if form.folderid and define.get_int(form.parentid) >= 0:
            folder.move(self.user_id, form)
        raise web.seeother("/manage/folders")


class control_ignoreuser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(username="")

        ignoreuser.insert(self.user_id, define.get_userid_list(form.username))
        raise web.seeother("/manage/ignore")


class control_unignoreuser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(username="")

        ignoreuser.remove(self.user_id, define.get_userid_list(form.username))
        raise web.seeother("/manage/ignore")


class control_streaming_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(target='')
        if form.target and self.user_id not in staff.MODS:
            return define.errorpage(self.user_id, errorcode.permission)
        elif form.target:
            target = define.get_int(form.target)
        else:
            target = self.user_id

        return define.webpage(self.user_id, "control/edit_streaming.html", [
            # Profile
            profile.select_profile(target, commish=False),
            form.target,
        ])

    @define.token_checked
    def POST(self):
        form = web.input(target="", set_stream="", stream_length="", stream_url="", stream_text="")

        if form.target and self.user_id not in staff.MODS:
            return define.errorpage(self.user_id, errorcode.permission)

        if form.target:
            target = int(form.target)
        else:
            target = self.user_id

        stream_length = define.clamp(define.get_int(form.stream_length), 0, 360)
        p = orm.Profile()
        p.stream_text = form.stream_text
        p.stream_url = define.text_fix_url(form.stream_url.strip())
        set_stream = form.set_stream

        profile.edit_streaming_settings(self.user_id, target, p,
                                        set_stream=set_stream,
                                        stream_length=stream_length)

        raise web.seeother("/control")


class control_apikeys_(controller_base):
    login_required = True
    disallow_api = True

    def GET(self):
        return define.webpage(self.user_id, "control/edit_apikeys.html", [
            api.get_api_keys(self.user_id),
            oauth2.get_consumers_for_user(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(**{'delete-api-keys': [], 'revoke-oauth2-consumers': []})

        if form.get('add-api-key'):
            api.add_api_key(self.user_id, form.get('add-key-description'))
        if form.get('delete-api-keys'):
            api.delete_api_keys(self.user_id, form['delete-api-keys'])
        if form.get('revoke-oauth2-consumers'):
            oauth2.revoke_consumers_for_user(self.user_id, form['revoke-oauth2-consumers'])

        raise web.seeother("/control/apikeys")


class manage_folders_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "manage/folders.html", [
            # Folders dropdown
            folder.select_list(self.user_id, "drop/all"),
        ])


class manage_following_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(userid="", backid="", nextid="")
        form.userid = define.get_int(form.userid)
        form.backid = define.get_int(form.backid)
        form.nextid = define.get_int(form.nextid)

        if form.userid:
            return define.webpage(self.user_id, "manage/following_user.html", [
                # Profile
                profile.select_profile(form.userid, avatar=True),
                # Follow settings
                followuser.select_settings(self.user_id, form.userid),
            ])
        else:
            return define.webpage(self.user_id, "manage/following_list.html", [
                # Following
                followuser.manage_following(self.user_id, 44, backid=form.backid, nextid=form.nextid),
            ])

    @define.token_checked
    def POST(self):
        form = web.input(userid="", submit="", collect="", char="", stream="", journal="")

        watch_settings = followuser.WatchSettings()
        watch_settings.submit = bool(form.submit)
        watch_settings.collect = bool(form.collect)
        watch_settings.char = bool(form.char)
        watch_settings.stream = bool(form.stream)
        watch_settings.journal = bool(form.journal)
        followuser.update(self.user_id, define.get_int(form.userid), watch_settings)

        raise web.seeother("/manage/following")


class manage_friends_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(feature="", backid="", nextid="")
        form.backid = define.get_int(form.backid)
        form.nextid = define.get_int(form.nextid)

        if form.feature == "pending":
            return define.webpage(self.user_id, "manage/friends_pending.html", [
                frienduser.select_requests(self.user_id, 20, backid=form.backid, nextid=form.nextid),
            ])
        else:
            return define.webpage(self.user_id, "manage/friends_accepted.html", [
                # Friends
                frienduser.select_accepted(self.user_id, 20, backid=form.backid, nextid=form.nextid),
            ])


class manage_ignore_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(feature="", backid="", nextid="")
        form.backid = define.get_int(form.backid)
        form.nextid = define.get_int(form.nextid)

        return define.webpage(self.user_id, "manage/ignore.html", [
            ignoreuser.select(self.user_id, 20, backid=form.backid, nextid=form.nextid),
        ])


class manage_collections_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(feature="", backid="", nextid="")
        backid = int(form.backid) if form.backid else None
        nextid = int(form.nextid) if form.nextid else None

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)

        if form.feature == "pending":
            return define.webpage(self.user_id, "manage/collections_pending.html", [
                # Pending Collections
                collection.select_list(self.user_id, rating, 30, otherid=self.user_id, backid=backid, nextid=nextid,
                                       pending=True, config=config),
                self.user_id
            ])

        return define.webpage(self.user_id, "manage/collections_accepted.html", [
            # Accepted Collections
            collection.select_list(self.user_id, rating, 30, otherid=self.user_id, backid=backid, nextid=nextid,
                                   config=config),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submissions=[], action="")
        # submissions input format: "submissionID;collectorID"
        # we have to split it apart because each offer on a submission is a single checkbox
        # but needs collector's ID for unambiguity
        intermediate = [x.split(";") for x in form.submissions]
        submissions = [(int(x[0]), int(x[1])) for x in intermediate]

        if form.action == "accept":
            collection.pending_accept(self.user_id, submissions)
        elif form.action == "reject":
            collection.pending_reject(self.user_id, submissions)
        else:
            raise WeasylError("Unexpected")

        raise web.seeother("/manage/collections?feature=pending")


class manage_thumbnail_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(submitid="", charid="", auto="")
        submitid = define.get_int(form.submitid)
        charid = define.get_int(form.charid)

        if submitid and self.user_id not in staff.ADMINS and self.user_id != define.get_ownerid(submitid=submitid):
            return define.errorpage(self.user_id, errorcode.permissions)
        elif charid and self.user_id not in staff.ADMINS and self.user_id != define.get_ownerid(charid=charid):
            return define.errorpage(self.user_id, errorcode.permissions)
        elif not submitid and not charid:
            return define.errorpage(self.user_id)

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

        options = ['imageselect']

        return define.webpage(self.user_id, "manage/thumbnail.html", [
            # Feature
            "submit" if submitid else "char",
            # Targetid
            define.get_targetid(submitid, charid),
            # Thumbnail
            source,
            # Exists
            bool(source),
        ], options=options)

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", charid="", x1="", y1="", x2="", y2="", thumbfile="")
        submitid = define.get_int(form.submitid)
        charid = define.get_int(form.charid)

        if submitid and self.user_id not in staff.ADMINS and self.user_id != define.get_ownerid(submitid=submitid):
            return define.errorpage(self.user_id)
        if charid and self.user_id not in staff.ADMINS and self.user_id != define.get_ownerid(charid=charid):
            return define.errorpage(self.user_id)
        if not submitid and not charid:
            return define.errorpage(self.user_id)

        if form.thumbfile:
            thumbnail.upload(self.user_id, form.thumbfile, submitid=submitid, charid=charid)
            if submitid:
                raise web.seeother("/manage/thumbnail?submitid=%i" % (submitid,))
            else:
                raise web.seeother("/manage/thumbnail?charid=%i" % (charid,))
        else:
            thumbnail.create(self.user_id, form.x1, form.y1, form.x2, form.y2, submitid=submitid, charid=charid)
            if submitid:
                raise web.seeother("/submission/%i" % (submitid,))
            else:
                raise web.seeother("/character/%i" % (charid,))


class manage_tagfilters_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "manage/tagfilters.html", [
            # Blocked tags
            blocktag.select(self.user_id),
            # filterable ratings
            profile.get_user_ratings(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(do="", title="", rating="")

        if form.do == "create":
            blocktag.insert(self.user_id, title=form.title, rating=define.get_int(form.rating))
        elif form.do == "remove":
            blocktag.remove(self.user_id, title=form.title)

        raise web.seeother("/manage/tagfilters")


class manage_avatar_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(style="")
        try:
            avatar_source = avatar.avatar_source(self.user_id)
        except WeasylError:
            avatar_source_url = None
        else:
            avatar_source_url = avatar_source['display_url']

        return define.webpage(
            self.user_id,
            "manage/avatar_nostyle.html" if form.style == "false" else "manage/avatar.html",
            [
                # Avatar selection
                avatar_source_url,
                # Avatar selection exists
                avatar_source_url is not None,
            ],
            options=["imageselect", "square_select"])

    @define.token_checked
    def POST(self):
        form = web.input(image="", x1=0, y1=0, x2=0, y2=0)

        avatar.create(self.user_id, form.x1, form.y1, form.x2, form.y2)
        raise web.seeother("/control")


class manage_banner_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "manage/banner.html")

    @define.token_checked
    def POST(self):
        form = web.input(image="")

        banner.upload(self.user_id, form.image)
        raise web.seeother("/control")


class manage_alias_(controller_base):
    login_required = True

    def GET(self):
        status = define.common_status_check(self.user_id)

        if status:
            return define.common_status_page(self.user_id, status)
        elif not self.user_id:
            return define.webpage(self.user_id)

        return define.webpage(self.user_id, "manage/alias.html", [
            # Alias
            useralias.select(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(username="")

        useralias.set(self.user_id, define.get_sysname(form.username))
        raise web.seeother("/control")


class sfwtoggle_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(redirect="/index")
        if api.is_api_user():
            raise web.webapi.Forbidden()

        currentstate = web.cookies(sfwmode="nsfw").sfwmode
        newstate = "sfw" if currentstate == "nsfw" else "nsfw"
        # cookie expires in 1 year
        web.setcookie("sfwmode", newstate, 31536000)
        # release the index page's cache so it shows the new ratings if they visit it
        index.template_fields.invalidate(self.user_id)
        raise web.seeother(form.redirect)

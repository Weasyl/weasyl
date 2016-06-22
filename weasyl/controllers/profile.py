import time

import web

from weasyl import (
    character, collection, commishinfo, define, errorcode, favorite, folder,
    followuser, frienduser, journal, media, profile, shout, submission,
    pagination)
from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import macro


# Profile browsing functions
class profile_(controller_base):
    def GET(self, name=""):
        now = time.time()

        form = web.input(userid="", name="")
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        extras = {
            "canonical_url": "/~" + define.get_sysname(form.name)
        }

        if define.user_is_twitterbot():
            extras['twitter_card'] = profile.twitter_card(otherid)
            extras['options'] = ['nocache']

        if not self.user_id and "h" in userprofile['config']:
            return define.errorpage(
                self.user_id,
                "You cannot view this page because the owner does not allow guests to view their profile.",
                **extras)

        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        extras['title'] = u"%s's profile" % (userprofile['full_name'] if has_fullname else userprofile['username'],)

        page = define.common_page_start(self.user_id, **extras)
        define.common_view_content(self.user_id, otherid, "profile")

        if 'O' in userprofile['config']:
            submissions = collection.select_list(
                self.user_id, rating, 11, otherid=otherid, options=["cover"], config=config)
            more_submissions = 'collections'
            featured = None
        elif 'A' in userprofile['config']:
            submissions = character.select_list(
                self.user_id, rating, 11, otherid=otherid, options=["cover"], config=config)
            more_submissions = 'characters'
            featured = None
        else:
            submissions = submission.select_list(
                self.user_id, rating, 11, otherid=otherid, options=["cover"], config=config,
                profile_page_filter=True)
            more_submissions = 'submissions'
            featured = submission.select_featured(self.user_id, otherid, rating)

        if userprofile['show_favorites_bar']:
            favorites = favorite.select_submit(self.user_id, rating, 11, otherid=otherid, config=config)
        else:
            favorites = None

        page.append(define.render('user/profile.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            macro.SOCIAL_SITES,
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Myself
            profile.select_myself(self.user_id),
            # Recent submissions
            submissions, more_submissions,
            favorites,
            featured,
            # Folders preview
            folder.select_preview(self.user_id, otherid, rating, 3),
            # Latest journal
            journal.select_latest(self.user_id, rating, otherid=otherid, config=config),
            # Recent shouts
            shout.select(self.user_id, ownerid=otherid, limit=8),
            # Statistics information
            profile.select_statistics(otherid),
            # Commission information
            commishinfo.select_list(otherid),
            # Friends
            frienduser.select(self.user_id, otherid, 5, choose=None),
            # Following
            followuser.select_following(self.user_id, otherid, choose=5),
            # Followed
            followuser.select_followed(self.user_id, otherid, choose=5),
        ]))

        return define.common_page_end(self.user_id, page, now=now)


class profile_media_(controller_base):
    def GET(self, name, link_type):
        userid = profile.resolve(None, None, name)
        media_items = media.get_user_media(userid)
        if not media_items.get(link_type):
            return web.notfound()
        web.header('X-Accel-Redirect', media_items[link_type][0]['file_url'])
        web.header('Cache-Control', 'max-age=0')
        return ''


class submissions_(controller_base):
    def GET(self, name=""):
        form = web.input(userid="", name="", backid=None, nextid=None, folderid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)
        folderid = define.get_int(form.folderid) or None

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's submissions" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        url_format = "/submissions/{username}?%s{folderquery}".format(
                     username=define.get_sysname(userprofile['username']),
                     folderquery="&folderid=%d" % folderid if folderid else "")
        result = pagination.PaginatedResult(
            submission.select_list, submission.select_count, 'submitid', url_format, self.user_id, rating,
            60, otherid=otherid, folderid=folderid, backid=define.get_int(form.backid),
            nextid=define.get_int(form.nextid), config=config, profile_page_filter=not folderid)

        page.append(define.render('user/submissions.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Recent submissions
            result,
            # Folders
            folder.select_list(otherid, "sidebar/all"),
            # Current folder
            folderid,
        ]))

        return define.common_page_end(self.user_id, page)


class collections_(controller_base):
    def GET(self, name=""):
        form = web.input(userid="", name="", backid=None, nextid=None,
                         folderid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's collections" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        url_format = "/collections?userid={userid}&%s".format(userid=userprofile['userid'])
        result = pagination.PaginatedResult(
            collection.select_list, collection.select_count, 'submitid', url_format, self.user_id, rating, 66,
            otherid=otherid, backid=define.get_int(form.backid), nextid=define.get_int(form.nextid), config=config)

        page.append(define.render('user/collections.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Collections
            result,
        ]))

        return define.common_page_end(self.user_id, page)


class journals_(controller_base):
    def GET(self, name=""):
        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's journals" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        page.append(define.render('user/journals.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Journals list
            # TODO(weykent): use select_user_list
            journal.select_list(self.user_id, rating, 250, otherid=otherid, config=config),
            # Latest journal
            journal.select_latest(self.user_id, rating, otherid=otherid),
        ]))

        return define.common_page_end(self.user_id, page)


class characters_(controller_base):
    def GET(self, name=""):

        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's characters" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        url_format = "/characters?userid={userid}&%s".format(userid=userprofile['userid'])
        result = pagination.PaginatedResult(
            character.select_list, character.select_count,
            'charid', url_format, self.user_id, rating, 60,
            otherid=otherid, backid=define.get_int(form.backid),
            nextid=define.get_int(form.nextid), config=config)

        page.append(define.render('user/characters.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Characters list
            result,
        ]))

        return define.common_page_end(self.user_id, page)


class shouts_(controller_base):
    def GET(self, name=""):
        now = time.time()

        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's shouts" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        page.append(define.render('user/shouts.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Myself
            profile.select_myself(self.user_id),
            # Comments
            shout.select(self.user_id, ownerid=otherid),
            # Feature
            "shouts",
        ]))

        return define.common_page_end(self.user_id, page, now=now)


class staffnotes_(controller_base):
    login_required = True
    moderator_only = True

    def GET(self, name=None):
        form = web.input(userid="")
        otherid = profile.resolve(self.user_id, define.get_int(form.userid), name)
        if not otherid:
            raise WeasylError("userRecordMissing")

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's staff notes" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        userinfo = profile.select_userinfo(otherid, config=userprofile['config'])
        reportstats = profile.select_report_stats(otherid)
        userinfo['reportstats'] = reportstats
        userinfo['reporttotal'] = sum(reportstats.values())

        page.append(define.render('user/shouts.html', [
            # Profile information
            userprofile,
            # User information
            userinfo,
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Myself
            profile.select_myself(self.user_id),
            # Comments
            shout.select(self.user_id, ownerid=otherid, staffnotes=True),
            # Feature
            "staffnotes",
        ]))

        return define.common_page_end(self.user_id, page, now=time.time())


class favorites_(controller_base):
    def GET(self, name=""):
        def _FEATURE(target):
            if target == "submit":
                return 10
            elif target == "char":
                return 20
            elif target == "journal":
                return 30
            else:
                return 0

        form = web.input(userid="", name="", feature="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        config = define.get_config(self.user_id)
        rating = define.get_rating(self.user_id)
        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)
        elif self.user_id != otherid and 'v' in define.get_config(otherid):
            return define.errorpage(
                self.user_id,
                "You cannot view this page because the owner does not allow anyone to see their favorites.")

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)
        has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
        page_title = u"%s's favorites" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
        page = define.common_page_start(self.user_id, title=page_title)

        if form.feature:
            nextid = define.get_int(form.nextid)
            backid = define.get_int(form.backid)
            url_format = (
                "/favorites?userid={userid}&feature={feature}&%s".format(userid=userprofile['userid'], feature=form.feature))
            id_field = form.feature + "id"

            count_function = None
            if form.feature == "submit":
                select_function = favorite.select_submit
                count_function = favorite.select_submit_count
            elif form.feature == "char":
                select_function = favorite.select_char
            elif form.feature == "journal":
                select_function = favorite.select_journal

            faves = pagination.PaginatedResult(
                select_function, count_function,
                id_field, url_format, self.user_id, rating, 60,
                otherid=otherid, backid=backid, nextid=nextid, config=config)
        else:
            faves = {
                "submit": favorite.select_submit(self.user_id, rating, 22, otherid=otherid, config=config),
                "char": favorite.select_char(self.user_id, rating, 22, otherid=otherid, config=config),
                "journal": favorite.select_journal(self.user_id, rating, 22, otherid=otherid, config=config),
            }

        page.append(define.render('user/favorites.html', [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Feature
            form.feature,
            # Favorites
            faves,
        ]))

        return define.common_page_end(self.user_id, page)


class friends_(controller_base):
    def GET(self, name=""):

        cachename = "user/friends.html"

        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)

        return define.webpage(self.user_id, cachename, [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Friends
            frienduser.select_friends(self.user_id, otherid, limit=44,
                                      backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
        ])


class following_(controller_base):
    def GET(self, name=""):
        cachename = "user/following.html"

        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)

        return define.webpage(self.user_id, cachename, [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Following
            followuser.select_following(self.user_id, otherid, limit=44,
                                        backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
        ])


class followed_(controller_base):
    def GET(self, name=""):
        cachename = "user/followed.html"

        form = web.input(userid="", name="", backid=None, nextid=None)
        form.name = name if name else form.name
        form.userid = define.get_int(form.userid)

        otherid = profile.resolve(self.user_id, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not self.user_id and "h" in define.get_config(otherid):
            return define.errorpage(self.user_id, errorcode.no_guest_access)

        userprofile = profile.select_profile(otherid, images=True, viewer=self.user_id)

        return define.webpage(self.user_id, cachename, [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(self.user_id, otherid),
            # Followed
            followuser.select_followed(self.user_id, otherid, limit=44,
                                       backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
        ])

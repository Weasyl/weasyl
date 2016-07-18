import time

from pyramid import httpexceptions
from pyramid.response import Response

from weasyl import (
    character, collection, commishinfo, define, errorcode, favorite, folder,
    followuser, frienduser, journal, macro, media, profile, shout, submission,
    pagination)
from weasyl.controllers.decorators import (
    login_required,
    moderator_only,
)
from weasyl.error import WeasylError


# Profile browsing functions
def profile_(request):
    now = time.time()

    form = request.web_input(userid="", name="")

    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    extras = {
        "canonical_url": "/~" + define.get_sysname(form.name)
    }

    if define.user_is_twitterbot():
        extras['twitter_card'] = profile.twitter_card(otherid)
        extras['options'] = ['nocache']

    if not request.userid and "h" in userprofile['config']:
        return Response(define.errorpage(
            request.userid,
            "You cannot view this page because the owner does not allow guests to view their profile.",
            **extras))

    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    extras['title'] = u"%s's profile" % (userprofile['full_name'] if has_fullname else userprofile['username'],)

    page = define.common_page_start(request.userid, **extras)
    define.common_view_content(request.userid, otherid, "profile")

    if 'O' in userprofile['config']:
        submissions = collection.select_list(
            request.userid, rating, 11, otherid=otherid, options=["cover"], config=config)
        more_submissions = 'collections'
        featured = None
    elif 'A' in userprofile['config']:
        submissions = character.select_list(
            request.userid, rating, 11, otherid=otherid, options=["cover"], config=config)
        more_submissions = 'characters'
        featured = None
    else:
        submissions = submission.select_list(
            request.userid, rating, 11, otherid=otherid, options=["cover"], config=config,
            profile_page_filter=True)
        more_submissions = 'submissions'
        featured = submission.select_featured(request.userid, otherid, rating)

    if userprofile['show_favorites_bar']:
        favorites = favorite.select_submit(request.userid, rating, 11, otherid=otherid, config=config)
    else:
        favorites = None

    page.append(define.render('user/profile.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        macro.SOCIAL_SITES,
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Myself
        profile.select_myself(request.userid),
        # Recent submissions
        submissions, more_submissions,
        favorites,
        featured,
        # Folders preview
        folder.select_preview(request.userid, otherid, rating, 3),
        # Latest journal
        journal.select_latest(request.userid, rating, otherid=otherid, config=config),
        # Recent shouts
        shout.select(request.userid, ownerid=otherid, limit=8),
        # Statistics information
        profile.select_statistics(otherid),
        # Commission information
        commishinfo.select_list(otherid),
        # Friends
        frienduser.select(request.userid, otherid, 5, choose=None),
        # Following
        followuser.select_following(request.userid, otherid, choose=5),
        # Followed
        followuser.select_followed(request.userid, otherid, choose=5),
    ]))

    return Response(define.common_page_end(request.userid, page, now=now))


def profile_media_(request):
    name = request.matchdict['name']
    link_type = request.matchdict['link_type']
    userid = profile.resolve(None, None, name)
    media_items = media.get_user_media(userid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()
    request.response.headers['X-Accel-Redirect'] = media_items[link_type][0]['file_url']
    request.response.headers['Cache-Control'] = 'max-age=0'
    return request.response


def submissions_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None, folderid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)
    folderid = define.get_int(form.folderid) or None

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's submissions" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/submissions/{username}?%s{folderquery}".format(
                 username=define.get_sysname(userprofile['username']),
                 folderquery="&folderid=%d" % folderid if folderid else "")
    result = pagination.PaginatedResult(
        submission.select_list, submission.select_count, 'submitid', url_format, request.userid, rating,
        60, otherid=otherid, folderid=folderid, backid=define.get_int(form.backid),
        nextid=define.get_int(form.nextid), config=config, profile_page_filter=not folderid)

    page.append(define.render('user/submissions.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Recent submissions
        result,
        # Folders
        folder.select_list(otherid, "sidebar/all"),
        # Current folder
        folderid,
    ]))

    return Response(define.common_page_end(request.userid, page))


def collections_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None,
                             folderid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.controller_baseselect_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's collections" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/collections?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        collection.select_list, collection.select_count, 'submitid', url_format, request.userid, rating, 66,
        otherid=otherid, backid=define.get_int(form.backid), nextid=define.get_int(form.nextid), config=config)

    page.append(define.render('user/collections.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Collections
        result,
    ]))

    return Response(define.common_page_end(request.userid, page))


def journals_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's journals" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    page.append(define.render('user/journals.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Journals list
        # TODO(weykent): use select_user_list
        journal.select_list(request.userid, rating, 250, otherid=otherid, config=config),
        # Latest journal
        journal.select_latest(request.userid, rating, otherid=otherid),
    ]))

    return Response(define.common_page_end(request.userid, page))


def characters_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's characters" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/characters?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        character.select_list, character.select_count,
        'charid', url_format, request.userid, rating, 60,
        otherid=otherid, backid=define.get_int(form.backid),
        nextid=define.get_int(form.nextid), config=config)

    page.append(define.render('user/characters.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Characters list
        result,
    ]))

    return Response(define.common_page_end(request.userid, page))


def shouts_(request):
    now = time.time()

    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's shouts" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    page.append(define.render('user/shouts.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Myself
        profile.select_myself(request.userid),
        # Comments
        shout.select(request.userid, ownerid=otherid),
        # Feature
        "shouts",
    ]))

    return Response(define.common_page_end(request.userid, page, now=now))


@login_required
@moderator_only
def staffnotes_(request):
    form = request.web_input(userid="")
    otherid = profile.resolve(request.userid, define.get_int(form.userid), request.matchdict.get('name', None))
    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's staff notes" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

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
        profile.select_relation(request.userid, otherid),
        # Myself
        profile.select_myself(request.userid),
        # Comments
        shout.select(request.userid, ownerid=otherid, staffnotes=True),
        # Feature
        "staffnotes",
    ]))

    return Response(define.common_page_end(request.userid, page, now=time.time()))


def favorites_(request):
    def _FEATURE(target):
        if target == "submit":
            return 10
        elif target == "char":
            return 20
        elif target == "journal":
            return 30
        else:
            return 0

    form = request.web_input(userid="", name="", feature="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    config = define.get_config(request.userid)
    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    # TODO(hyena): Why aren't more of these WeasylErrors?
    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))
    elif request.userid != otherid and 'v' in define.get_config(otherid):
        return Response(define.errorpage(
            request.userid,
            "You cannot view this page because the owner does not allow anyone to see their favorites."))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's favorites" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

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
            id_field, url_format, request.userid, rating, 60,
            otherid=otherid, backid=backid, nextid=nextid, config=config)
    else:
        faves = {
            "submit": favorite.select_submit(request.userid, rating, 22, otherid=otherid, config=config),
            "char": favorite.select_char(request.userid, rating, 22, otherid=otherid, config=config),
            "journal": favorite.select_journal(request.userid, rating, 22, otherid=otherid, config=config),
        }

    page.append(define.render('user/favorites.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Feature
        form.feature,
        # Favorites
        faves,
    ]))

    return Response(define.common_page_end(request.userid, page))


def friends_(request):
        cachename = "user/friends.html"

        form = request.web_input(userid="", name="", backid=None, nextid=None)
        form.name = request.matchdict.get('name', form.name)
        form.userid = define.get_int(form.userid)

        otherid = profile.resolve(request.userid, form.userid, form.name)

        if not otherid:
            raise WeasylError("userRecordMissing")
        elif not request.userid and "h" in define.get_config(otherid):
            return Response(define.errorpage(request.userid, errorcode.no_guest_access))

        userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)

        return Response(define.webpage(request.userid, cachename, [
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            profile.select_relation(request.userid, otherid),
            # Friends
            frienduser.select_friends(request.userid, otherid, limit=44,
                                      backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
        ]))


def following_(request):
    cachename = "user/following.html"

    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)

    return Response(define.webpage(request.userid, cachename, [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Following
        followuser.select_following(request.userid, otherid, limit=44,
                                    backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
    ]))


def followed_(request):
    cachename = "user/followed.html"

    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        return Response(define.errorpage(request.userid, errorcode.no_guest_access))

    userprofile = profile.select_profile(otherid, images=True, viewer=request.userid)

    return Response(define.webpage(request.userid, cachename, [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        profile.select_relation(request.userid, otherid),
        # Followed
        followuser.select_followed(request.userid, otherid, limit=44,
                                   backid=define.get_int(form.backid), nextid=define.get_int(form.nextid)),
    ]))

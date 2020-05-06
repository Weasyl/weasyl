from __future__ import absolute_import

from pyramid import httpexceptions
from pyramid.response import Response

from weasyl import (
    character, collection, commishinfo, define, favorite, folder,
    followuser, frienduser, journal, macro, media, profile, shout, submission,
    pagination)
from weasyl.controllers.decorators import moderator_only
from weasyl.error import WeasylError


# Profile browsing functions
def profile_(request):
    form = request.web_input(userid="", name="")

    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, viewer=request.userid)

    if otherid != request.userid and not define.is_vouched_for(otherid):
        can_vouch = request.userid != 0 and define.is_vouched_for(request.userid)

        return Response(
            define.webpage(
                request.userid,
                "error/unverified.html",
                [request, otherid, userprofile['username'], can_vouch],
            ),
            status=403,
        )

    extras = {
        "canonical_url": "/~" + define.get_sysname(userprofile['username'])
    }

    if not request.userid:
        # Only generate the Twitter/OGP meta headers if not authenticated (the UA viewing is likely automated).
        twit_card = profile.twitter_card(otherid)
        if define.user_is_twitterbot():
            extras['twitter_card'] = twit_card
        # The "og:" prefix is specified in page_start.html, and og:image is required by the OGP spec, so something must be in there.
        extras['ogp'] = {
            'title': twit_card['title'],
            'site_name': "Weasyl",
            'type': "website",
            'url': twit_card['url'],
            'description': twit_card['description'],
            'image': twit_card['image:src'] if 'image:src' in twit_card else define.get_resource_url('img/logo-mark-light.svg'),
        }

    if not request.userid and "h" in userprofile['config']:
        raise WeasylError('noGuests')

    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    extras['title'] = u"%s's profile" % (userprofile['full_name'] if has_fullname else userprofile['username'],)

    page = define.common_page_start(request.userid, **extras)
    define.common_view_content(request.userid, otherid, "profile")

    if 'O' in userprofile['config']:
        submissions = collection.select_list(request.userid, rating, 11, otherid=otherid)
        more_submissions = 'collections'
        featured = None
    elif 'A' in userprofile['config']:
        submissions = character.select_list(request.userid, rating, 11, otherid=otherid)
        more_submissions = 'characters'
        featured = None
    else:
        submissions = submission.select_list(
            request.userid, rating, 11, otherid=otherid,
            profile_page_filter=True)
        more_submissions = 'submissions'
        featured = submission.select_featured(request.userid, otherid, rating)

    if userprofile['show_favorites_bar']:
        favorites = favorite.select_submit(request.userid, rating, 11, otherid=otherid)
    else:
        favorites = None

    statistics, show_statistics = profile.select_statistics(otherid)

    page.append(define.render('user/profile.html', [
        request,
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
        folder.select_preview(request.userid, otherid, rating),
        # Latest journal
        journal.select_latest(request.userid, rating, otherid=otherid),
        # Recent shouts
        shout.select(request.userid, ownerid=otherid, limit=8),
        # Statistics information
        statistics,
        show_statistics,
        # Commission information
        commishinfo.select_list(otherid),
        # Friends
        lambda: frienduser.has_friends(otherid),
    ]))

    return Response(define.common_page_end(request.userid, page))


def profile_media_(request):
    name = request.matchdict['name']
    link_type = request.matchdict['link_type']
    userid = profile.resolve(None, None, name)
    media_items = media.get_user_media(userid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()
    return Response(headerlist=[
        ('X-Accel-Redirect', str(media_items[link_type][0]['file_url']),),
        ('Cache-Control', 'max-age=0',),
    ])


def submissions_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None, folderid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)
    folderid = define.get_int(form.folderid) or None

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's submissions" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/submissions/{username}?%s{folderquery}".format(
                 username=define.get_sysname(userprofile['username']),
                 folderquery="&folderid=%d" % folderid if folderid else "")
    result = pagination.PaginatedResult(
        submission.select_list, submission.select_count, 'submitid', url_format, request.userid, rating,
        60, otherid=otherid, folderid=folderid, backid=define.get_int(form.backid),
        nextid=define.get_int(form.nextid), profile_page_filter=not folderid)

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

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's collections" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/collections?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        collection.select_list, collection.select_count, 'submitid', url_format, request.userid, rating, 66,
        otherid=otherid, backid=define.get_int(form.backid), nextid=define.get_int(form.nextid))

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

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
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
        journal.select_list(request.userid, rating, 250, otherid=otherid),
    ]))

    return Response(define.common_page_end(request.userid, page))


def characters_(request):
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's characters" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/characters?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        character.select_list, character.select_count,
        'charid', url_format, request.userid, rating, 60,
        otherid=otherid, backid=define.get_int(form.backid),
        nextid=define.get_int(form.nextid))

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
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)

    if otherid != request.userid and not define.is_vouched_for(otherid):
        can_vouch = request.userid != 0 and define.is_vouched_for(request.userid)

        return Response(
            define.webpage(
                request.userid,
                "error/unverified.html",
                [request, otherid, userprofile['username'], can_vouch],
            ),
            status=403,
        )

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

    return Response(define.common_page_end(request.userid, page))


@moderator_only
def staffnotes_(request):
    form = request.web_input(userid="")
    otherid = profile.resolve(request.userid, define.get_int(form.userid), request.matchdict.get('name', None))
    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, viewer=request.userid)
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

    return Response(define.common_page_end(request.userid, page))


def favorites_(request):
    form = request.web_input(userid="", name="", feature="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, form.userid, form.name)

    # TODO(hyena): Why aren't more of these WeasylErrors?
    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')
    elif request.userid != otherid and 'v' in define.get_config(otherid):
        raise WeasylError('hiddenFavorites')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = u"%s's favorites" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    if form.feature:
        nextid = define.get_int(form.nextid)
        backid = define.get_int(form.backid)
        url_format = (
            "/favorites?userid={userid}&feature={feature}&%s".format(userid=otherid, feature=form.feature))
        id_field = form.feature + "id"

        count_function = None
        if form.feature == "submit":
            select_function = favorite.select_submit
            count_function = favorite.select_submit_count
        elif form.feature == "char":
            select_function = favorite.select_char
        elif form.feature == "journal":
            select_function = favorite.select_journal
        else:
            raise httpexceptions.HTTPNotFound()

        faves = pagination.PaginatedResult(
            select_function, count_function,
            id_field, url_format, request.userid, rating, 60,
            otherid=otherid, backid=backid, nextid=nextid)
    else:
        faves = {
            "submit": favorite.select_submit(request.userid, rating, 22, otherid=otherid),
            "char": favorite.select_char(request.userid, rating, 22, otherid=otherid),
            "journal": favorite.select_journal(request.userid, rating, 22, otherid=otherid),
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
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)

    return Response(define.webpage(request.userid, "user/friends.html", [
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
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)

    return Response(define.webpage(request.userid, "user/following.html", [
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
    form = request.web_input(userid="", name="", backid=None, nextid=None)
    form.name = request.matchdict.get('name', form.name)
    form.userid = define.get_int(form.userid)

    otherid = profile.resolve(request.userid, form.userid, form.name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)

    return Response(define.webpage(request.userid, "user/followed.html", [
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

from pyramid import httpexceptions
from pyramid.response import Response

from libweasyl import staff
from libweasyl.text import markdown_excerpt

from weasyl import (
    character, collection, commishinfo, define, favorite, folder,
    followuser, frienduser, journal, media, profile, shout, submission,
    pagination)
from weasyl.controllers.decorators import moderator_only
from weasyl.error import WeasylError


def _get_post_counts_by_type(userid, *, friends: bool, rating):
    result = {
        "submission": 0,
        "journal": 0,
        "character": 0,
        "collection": 0,
    }

    for key, count in define.posts_count(userid, friends=friends).items():
        if key.rating <= rating:
            result[key.post_type] += count

    return result


# Profile browsing functions
def profile_(request):
    name = request.params.get('name', '')
    name = request.matchdict.get('name', name)
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)

    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    is_unverified = otherid != request.userid and not define.is_vouched_for(otherid)

    if is_unverified and request.userid not in staff.MODS:
        can_vouch = request.userid != 0 and define.is_vouched_for(request.userid)

        return Response(
            define.webpage(
                request.userid,
                "error/unverified.html",
                [request, otherid, userprofile['username'], can_vouch],
            ),
            status=403,
        )

    if not request.userid and "h" in userprofile['config']:
        raise WeasylError('noGuests')

    username = userprofile["username"]
    canonical_path = request.route_path("profile_tilde", name=define.get_sysname(username))
    title = f"{username}’s profile"
    meta_description = markdown_excerpt(userprofile["profile_text"])
    avatar_url = define.absolutify_url(userprofile['user_media']['avatar'][0]['display_url'])
    twitter_meta = {
        "card": "summary",
        "title": title,
        "image": avatar_url,
    }
    ogp = {
        "title": title,
        "type": "profile",
        "url": define.absolutify_url(canonical_path),
        "image": avatar_url,
        "username": username,
    }

    if twitter_username := profile.get_twitter_username(otherid):
        twitter_meta["creator"] = "@" + twitter_username

    if meta_description:
        twitter_meta["description"] = ogp["description"] = meta_description

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
            request.userid, rating, limit=11, otherid=otherid,
            profile_page_filter=True)
        more_submissions = 'submissions'
        featured = submission.select_featured(request.userid, otherid, rating)

    if userprofile['show_favorites_bar']:
        favorites = favorite.select_submit(request.userid, rating, 11, otherid=otherid)
    else:
        favorites = None

    statistics, show_statistics = profile.select_statistics(otherid)

    relation = profile.select_relation(request.userid, otherid)

    return Response(define.webpage(
        request.userid,
        "user/profile.html",
        (
            request,
            # Profile information
            userprofile,
            # User information
            profile.select_userinfo(otherid, config=userprofile['config']),
            # Relationship
            relation,
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
            is_unverified,
            _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
        ),
        twitter_card=twitter_meta,
        ogp=ogp,
        canonical_url=canonical_path,
        title=title,
    ))


def profile_media_(request):
    name = request.matchdict['name']
    link_type = request.matchdict['link_type']
    userid = profile.resolve_by_username(name)
    media_items = media.get_user_media(userid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()
    return Response(headerlist=[
        ('X-Accel-Redirect', str(media_items[link_type][0]['file_url']),),
        ('Cache-Control', 'max-age=0',),
    ])


def submissions_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)
    folderid = define.get_int(request.params.get('folderid')) or None
    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's submissions" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/submissions/{username}?%s{folderquery}".format(
                 username=define.get_sysname(userprofile['username']),
                 folderquery="&folderid=%d" % folderid if folderid else "")
    result = pagination.PaginatedResult(
        submission.select_list, submission.select_count, 'submitid', url_format, request.userid, rating,
        limit=60, otherid=otherid, folderid=folderid, backid=define.get_int(backid),
        nextid=define.get_int(nextid), profile_page_filter=not folderid,
        count_limit=submission.COUNT_LIMIT)

    relation = profile.select_relation(request.userid, otherid)

    page.append(define.render('user/submissions.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Recent submissions
        result,
        # Folders
        folder.select_list(otherid),
        # Current folder
        folderid,
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def collections_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's collections" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/collections?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        collection.select_list, collection.select_count, 'submitid', url_format, request.userid, rating,
        limit=66, otherid=otherid, backid=define.get_int(backid), nextid=define.get_int(nextid))

    relation = profile.select_relation(request.userid, otherid)

    page.append(define.render('user/collections.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Collections
        result,
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def journals_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's journals" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    relation = profile.select_relation(request.userid, otherid)

    page.append(define.render('user/journals.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Journals list
        journal.select_list(request.userid, rating, otherid=otherid),
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def characters_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's characters" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    url_format = "/characters?userid={userid}&%s".format(userid=userprofile['userid'])
    result = pagination.PaginatedResult(
        character.select_list, character.select_count,
        'charid', url_format, request.userid, rating,
        limit=60,
        otherid=otherid, backid=define.get_int(backid),
        nextid=define.get_int(nextid))

    relation = profile.select_relation(request.userid, otherid)

    page.append(define.render('user/characters.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Characters list
        result,
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def shouts_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    otherid = profile.resolve(request.userid, userid, name)

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
    page_title = "%s's shouts" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    relation = profile.select_relation(request.userid, otherid)
    rating = define.get_rating(request.userid)

    page.append(define.render('user/shouts.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Myself
        profile.select_myself(request.userid),
        # Comments
        shout.select(request.userid, ownerid=otherid),
        # Feature
        "shouts",
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


@moderator_only
def staffnotes_(request):
    userid = define.get_int(request.params.get('userid'))
    otherid = profile.resolve(request.userid, define.get_int(userid), request.matchdict.get('name', None))
    if not otherid:
        raise WeasylError("userRecordMissing")

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's staff notes" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    userinfo = profile.select_userinfo(otherid, config=userprofile['config'])
    reportstats = profile.select_report_stats(otherid)
    userinfo['reportstats'] = reportstats
    userinfo['reporttotal'] = sum(reportstats.values())

    relation = profile.select_relation(request.userid, otherid)
    rating = define.get_rating(request.userid)

    page.append(define.render('user/shouts.html', [
        # Profile information
        userprofile,
        # User information
        userinfo,
        # Relationship
        relation,
        # Myself
        profile.select_myself(request.userid),
        # Comments
        shout.select(request.userid, ownerid=otherid, staffnotes=True),
        # Feature
        "staffnotes",
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def favorites_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    rating = define.get_rating(request.userid)
    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    feature = request.params.get('feature', False)

    # TODO(hyena): Why aren't more of these WeasylErrors?
    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')
    elif request.userid != otherid and 'v' in define.get_config(otherid):
        raise WeasylError('hiddenFavorites')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    has_fullname = userprofile['full_name'] is not None and userprofile['full_name'].strip() != ''
    page_title = "%s's favorites" % (userprofile['full_name'] if has_fullname else userprofile['username'],)
    page = define.common_page_start(request.userid, title=page_title)

    if feature:
        nextid = define.get_int(nextid)
        backid = define.get_int(backid)
        url_format = (
            "/favorites?userid={userid}&feature={feature}&%s".format(userid=otherid, feature=feature))
        id_field = feature + "id"

        count_function = None
        if feature == "submit":
            select_function = favorite.select_submit
            count_function = favorite.select_submit_count
        elif feature == "char":
            select_function = favorite.select_char
        elif feature == "journal":
            select_function = favorite.select_journal
        else:
            raise httpexceptions.HTTPNotFound()

        faves = pagination.PaginatedResult(
            select_function, count_function,
            id_field, url_format, request.userid, rating,
            limit=60, otherid=otherid, backid=backid, nextid=nextid)
    else:
        faves = {
            "submit": favorite.select_submit(request.userid, rating, 22, otherid=otherid),
            "char": favorite.select_char(request.userid, rating, 22, otherid=otherid),
            "journal": favorite.select_journal(request.userid, rating, 22, otherid=otherid),
        }

    relation = profile.select_relation(request.userid, otherid)

    page.append(define.render('user/favorites.html', [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Feature
        feature,
        # Favorites
        faves,
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

    return Response(define.common_page_end(request.userid, page))


def friends_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    relation = profile.select_relation(request.userid, otherid)
    rating = define.get_rating(request.userid)

    return Response(define.webpage(request.userid, "user/friends.html", [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Friends
        frienduser.select_friends(request.userid, otherid, limit=44,
                                  backid=define.get_int(backid), nextid=define.get_int(nextid)),
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))


def following_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    relation = profile.select_relation(request.userid, otherid)
    rating = define.get_rating(request.userid)

    return Response(define.webpage(request.userid, "user/following.html", [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Following
        followuser.select_following(request.userid, otherid, limit=44,
                                    backid=define.get_int(backid), nextid=define.get_int(nextid)),
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))


def followed_(request):
    name = request.matchdict.get('name', request.params.get('name', ''))
    userid = define.get_int(request.params.get('userid'))

    otherid = profile.resolve(request.userid, userid, name)

    backid = request.params.get('backid')
    nextid = request.params.get('nextid')

    if not otherid:
        raise WeasylError("userRecordMissing")
    elif not request.userid and "h" in define.get_config(otherid):
        raise WeasylError('noGuests')

    userprofile = profile.select_profile(otherid, viewer=request.userid)
    relation = profile.select_relation(request.userid, otherid)
    rating = define.get_rating(request.userid)

    return Response(define.webpage(request.userid, "user/followed.html", [
        # Profile information
        userprofile,
        # User information
        profile.select_userinfo(otherid, config=userprofile['config']),
        # Relationship
        relation,
        # Followed
        followuser.select_followed(request.userid, otherid, limit=44,
                                   backid=define.get_int(backid), nextid=define.get_int(nextid)),
        _get_post_counts_by_type(otherid, friends=relation["friend"], rating=rating),
    ]))

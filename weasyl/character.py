import arrow

from libweasyl import images
from libweasyl import ratings
from libweasyl import staff
from libweasyl import text

from weasyl import api
from weasyl import blocktag
from weasyl import comment
from weasyl import define
from weasyl import favorite
from weasyl import files
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import image
from weasyl import macro
from weasyl import media
from weasyl import profile
from weasyl import report
from weasyl import searchtag
from weasyl import thumbnail
from weasyl import welcome
from weasyl.error import PostgresError, WeasylError


_MEGABYTE = 1048576
_MAIN_IMAGE_SIZE_LIMIT = 50 * _MEGABYTE


def create(userid, character, friends, tags, thumbfile, submitfile):
    # Make temporary filenames
    tempthumb = files.get_temporary(userid, "thumb")
    tempsubmit = files.get_temporary(userid, "char")

    # Determine filesizes
    thumbsize = len(thumbfile)
    submitsize = len(submitfile)

    # Check invalid title or rating
    if not character.char_name:
        raise WeasylError("characterNameInvalid")
    elif not character.rating:
        raise WeasylError("ratingInvalid")
    profile.check_user_rating_allowed(userid, character.rating)
    if character.rating.minimum_age:
        profile.assert_adult(userid)

    # Write temporary thumbnail file
    if thumbsize:
        files.write(tempthumb, thumbfile)
        thumbextension = files.get_extension_for_category(
            thumbfile, macro.ART_SUBMISSION_CATEGORY)
    else:
        thumbextension = None

    # Write temporary submission file
    if submitsize:
        files.write(tempsubmit, submitfile)
        submitextension = files.get_extension_for_category(
            submitfile, macro.ART_SUBMISSION_CATEGORY)
    else:
        submitextension = None

    # Check invalid file data
    if not submitsize:
        files.clear_temporary(userid)
        raise WeasylError("submitSizeZero")
    elif submitsize > _MAIN_IMAGE_SIZE_LIMIT:
        files.clear_temporary(userid)
        raise WeasylError("submitSizeExceedsLimit")
    elif thumbsize > 10 * _MEGABYTE:
        files.clear_temporary(userid)
        raise WeasylError("thumbSizeExceedsLimit")
    elif submitextension not in [".jpg", ".png", ".gif"]:
        files.clear_temporary(userid)
        raise WeasylError("submitType")
    elif thumbsize and thumbextension not in [".jpg", ".png", ".gif"]:
        files.clear_temporary(userid)
        raise WeasylError("thumbType")

    # Assign settings
    settings = (
        files.typeflag("submit", submitextension)
        + files.typeflag("cover", submitextension)
    )

    # Insert submission data
    ch = define.meta.tables["character"]

    try:
        charid = define.engine.scalar(ch.insert().returning(ch.c.charid), {
            "userid": userid,
            "unixtime": arrow.utcnow(),
            "char_name": character.char_name,
            "age": character.age,
            "gender": character.gender,
            "height": character.height,
            "weight": character.weight,
            "species": character.species,
            "content": character.content,
            "rating": character.rating.code,
            "settings": settings,
            "hidden": False,
            "friends_only": friends,
        })
    except PostgresError:
        files.clear_temporary(userid)
        raise

    # Assign search tags
    searchtag.associate(
        userid=userid,
        target=searchtag.CharacterTarget(charid),
        tag_names=tags,
    )

    # Make submission file
    files.make_character_directory(charid)
    files.copy(tempsubmit, files.make_resource(userid, charid, "char/submit", submitextension))

    # Make cover file
    image.make_cover(tempsubmit, files.make_resource(userid, charid, "char/cover", submitextension))

    # Make thumbnail selection file
    if thumbsize:
        image.make_cover(
            tempthumb, files.make_resource(userid, charid, "char/.thumb"))

    thumbnail.create(0, 0, 0, 0, charid=charid, remove=False)

    # Create notifications
    welcome.character_insert(userid, charid, rating=character.rating.code,
                             friends_only=friends)

    # Clear temporary files
    files.clear_temporary(userid)

    define.metric('increment', 'characters')
    define.cached_posts_count.invalidate(userid)

    return charid


def reupload(userid, charid, submitdata):
    submitsize = len(submitdata)
    if not submitsize:
        raise WeasylError("submitSizeZero")
    elif submitsize > _MAIN_IMAGE_SIZE_LIMIT:
        raise WeasylError("submitSizeExceedsLimit")

    # Select character data
    query, = define.engine.execute("""
        SELECT userid, settings FROM character WHERE charid = %(character)s AND NOT hidden
    """, character=charid)

    if userid != query.userid:
        raise WeasylError("Unexpected")

    im = image.from_string(submitdata)
    submitextension = images.image_extension(im)

    # Check invalid file data
    if not submitextension:
        raise WeasylError("submitType")

    # Make submission file
    submitfile = files.make_resource(userid, charid, "char/submit", submitextension)
    files.ensure_file_directory(submitfile)
    im.write(submitfile)

    # Make cover file
    image.make_cover(
        submitfile, files.make_resource(userid, charid, "char/cover", submitextension))

    # Update settings
    settings = (
        files.typeflag("submit", submitextension)
        + files.typeflag("cover", submitextension)
    )
    define.engine.execute("""
        UPDATE character
           SET settings = %(settings)s
         WHERE charid = %(character)s
    """, settings=settings, character=charid)


def _select_character_and_check(userid, charid, *, rating, ignore, anyway, increment_views=True):
    """Selects a character, after checking if the user is authorized, etc.

    Args:
        userid (int): Currently authenticating user ID.
        charid (int): Character ID to fetch.
        rating (int): Maximum rating to display.
        ignore (bool): Whether to respect ignored or blocked tags
        anyway (bool): Whether to ignore checks and display anyway.
        increment_views (bool): Whether to increment the number of views on the submission. Defaults to True.

    Returns:
        A character and all needed data as a dict.
    """
    query = define.engine.execute("""
        SELECT
            ch.userid, pr.username, ch.unixtime, ch.char_name, ch.age, ch.gender, ch.height, ch.weight, ch.species,
            ch.content, ch.rating, ch.settings, ch.hidden, ch.friends_only, ch.page_views
        FROM character ch
            INNER JOIN profile pr USING (userid)
        WHERE ch.charid = %(charid)s
    """, charid=charid).first()

    if query and userid in staff.MODS and anyway:
        pass
    elif not query or query.hidden:
        raise WeasylError('characterRecordMissing')
    elif query.rating > rating and ((userid != query.userid and userid not in staff.MODS) or define.is_sfw_mode()):
        raise WeasylError('RatingExceeded')
    elif query.friends_only and not frienduser.check(userid, query.userid):
        raise WeasylError('FriendsOnly')
    elif ignore and ignoreuser.check(userid, query.userid):
        raise WeasylError('UserIgnored')
    elif ignore and blocktag.check(userid, charid=charid):
        raise WeasylError('TagBlocked')

    query = dict(query)

    if increment_views and define.common_view_content(userid, charid, 'char'):
        query['page_views'] += 1

    return query


def select_view(userid, charid, rating, ignore=True, anyway=None):
    query = _select_character_and_check(
        userid, charid, rating=rating, ignore=ignore, anyway=anyway == "true")

    login = define.get_sysname(query['username'])

    return {
        'charid': charid,
        'userid': query['userid'],
        'username': query['username'],
        'user_media': media.get_user_media(query['userid']),
        'mine': userid == query['userid'],
        'unixtime': query['unixtime'],
        'title': query['char_name'],
        'age': query['age'],
        'gender': query['gender'],
        'height': query['height'],
        'weight': query['weight'],
        'species': query['species'],
        'content': query['content'],
        'rating': query['rating'],
        'reported': report.check(charid=charid),
        'favorited': favorite.check(userid, charid=charid),
        'page_views': query['page_views'],
        'friends_only': query['friends_only'],
        'hidden': query['hidden'],
        'fave_count': favorite.count(charid, 'character'),
        'comments': comment.select(userid, charid=charid),
        'sub_media': fake_media_items(
            charid, query['userid'], login, query['settings']),
        'tags': searchtag.select_grouped(userid, searchtag.CharacterTarget(charid)),
    }


def select_view_api(userid, charid, anyway=False, increment_views=False):
    rating = define.get_rating(userid)

    query = _select_character_and_check(
        userid, charid, rating=rating, ignore=anyway,
        anyway=anyway, increment_views=increment_views)

    login = define.get_sysname(query['username'])

    return {
        'charid': charid,
        'owner': query['username'],
        'owner_login': login,
        'owner_media': api.tidy_all_media(
            media.get_user_media(query['userid'])),
        'posted_at': define.iso8601(query['unixtime']),
        'title': query['char_name'],
        'age': query['age'],
        'gender': query['gender'],
        'height': query['height'],
        'weight': query['weight'],
        'species': query['species'],
        'content': text.markdown(query['content']),
        'rating': ratings.CODE_TO_NAME[query['rating']],
        'favorited': favorite.check(userid, charid=charid),
        'views': query['page_views'],
        'friends_only': query['friends_only'],
        'favorites': favorite.count(charid, 'character'),
        'comments': comment.count(charid, 'character'),
        'media': api.tidy_all_media(fake_media_items(
            charid, query['userid'], login, query['settings'])),
        'tags': searchtag.select(charid=charid),
        'type': 'character',
        'link': define.absolutify_url(
            '/character/%d/%s' % (charid, text.slug_for(query['char_name']))),
    }


def select_query(userid, rating, otherid=None, backid=None, nextid=None):
    statement = [" FROM character ch INNER JOIN profile pr ON ch.userid = pr.userid WHERE NOT ch.hidden"]

    # Ignored users and blocked tags
    if userid:
        # filter own content in SFW mode
        if define.is_sfw_mode():
            statement.append(" AND (ch.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (ch.rating <= %i OR ch.userid = %i)" % (rating, userid))
        if not otherid:
            statement.append(macro.MACRO_IGNOREUSER % (userid, "ch"))
        statement.append(macro.MACRO_BLOCKTAG_CHAR % (userid, userid))
        statement.append(macro.MACRO_FRIENDUSER_CHARACTER % (userid, userid, userid))
    else:
        statement.append(" AND ch.rating <= %i AND NOT ch.friends_only" % (rating,))

    # Content owner
    if otherid:
        statement.append(" AND ch.userid = %i" % (otherid,))

    # Browse selection
    if backid:
        statement.append(" AND ch.charid > %i" % (backid,))
    elif nextid:
        statement.append(" AND ch.charid < %i" % (nextid,))

    return statement


def select_count(userid, rating, otherid=None, backid=None, nextid=None):
    statement = ["SELECT count(ch.charid)"]
    statement.extend(select_query(userid, rating, otherid, backid, nextid))
    return define.execute("".join(statement))[0][0]


def select_list(userid, rating, limit, otherid=None, backid=None, nextid=None):
    statement = ["SELECT ch.charid, ch.char_name, ch.rating, ch.unixtime, ch.userid, pr.username, ch.settings "]
    statement.extend(select_query(userid, rating, otherid, backid, nextid))

    statement.append(" ORDER BY ch.charid%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = []
    for i in define.execute("".join(statement)):
        query.append({
            "contype": 20,
            "charid": i[0],
            "title": i[1],
            "rating": i[2],
            "unixtime": i[3],
            "userid": i[4],
            "username": i[5],
            "sub_media": fake_media_items(i[0], i[4], define.get_sysname(i[5]), i[6]),
        })

    return query[::-1] if backid else query


def edit(userid, character, friends_only):
    query = define.engine.execute("SELECT userid, hidden FROM character WHERE charid = %(id)s",
                                  id=character.charid).first()

    if not query or query.hidden:
        raise WeasylError("Unexpected")
    elif userid != query.userid and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    elif not character.char_name:
        raise WeasylError("characterNameInvalid")
    elif not character.rating:
        raise WeasylError("Unexpected")

    if userid == query.userid:
        profile.check_user_rating_allowed(userid, character.rating)
        if character.rating.minimum_age:
            profile.assert_adult(userid)

    if friends_only:
        welcome.character_remove(character.charid)

    ch = define.meta.tables["character"]
    define.engine.execute(
        ch.update()
        .where(ch.c.charid == character.charid)
        .values({
            'char_name': character.char_name,
            'age': character.age,
            'gender': character.gender,
            'height': character.height,
            'weight': character.weight,
            'species': character.species,
            'content': character.content,
            'rating': character.rating,
            'friends_only': friends_only,
        })
    )

    if userid != query.userid:
        from weasyl import moderation
        moderation.note_about(
            userid, query.userid, 'The following character was edited:',
            '- ' + text.markdown_link(character.char_name, '/character/%s?anyway=true' % (character.charid,)))

    define.cached_posts_count.invalidate(query.userid)


def remove(userid, charid):
    ownerid = define.get_ownerid(charid=charid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    result = define.engine.execute(
        "UPDATE character SET hidden = TRUE WHERE charid = %(charid)s AND NOT hidden",
        {"charid": charid},
    )

    if result.rowcount != 0:
        welcome.character_remove(charid)
        define.cached_posts_count.invalidate(ownerid)

    return ownerid


def fake_media_items(charid, userid, login, settings):
    submission_url = define.cdnify_url(define.url_make(
        charid, "char/submit", query=[userid, settings], file_prefix=login))
    cover_url = define.cdnify_url(define.url_make(
        charid, "char/cover", query=[settings], file_prefix=login))
    thumbnail_url = define.cdnify_url(define.url_make(
        charid, "char/thumb", query=[settings]))

    return {
        "submission": [{
            "display_url": submission_url,
        }],
        "thumbnail-generated": [{
            "display_url": thumbnail_url,
        }],
        "cover": [{
            "display_url": cover_url,
        }],
    }

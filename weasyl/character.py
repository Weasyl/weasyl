# character.py

import arrow
import re

from error import PostgresError, WeasylError
import macro
import define

import image
import comment
import profile
import welcome
import blocktag
import searchtag
import thumbnail
import frienduser
import ignoreuser

import files
import report
import favorite

from libweasyl import staff, text

from weasyl import macro as m
from weasyl import media, api


_MEGABYTE = 1048576


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

    # Write temporary thumbnail file
    if thumbsize:
        files.easyupload(tempthumb, thumbfile, "image")
        thumbextension = files.get_extension_for_category(
            thumbfile, m.ART_SUBMISSION_CATEGORY)
    else:
        thumbextension = None

    # Write temporary submission file
    if submitsize:
        files.easyupload(tempsubmit, submitfile, "image")
        submitextension = files.get_extension_for_category(
            submitfile, m.ART_SUBMISSION_CATEGORY)
    else:
        submitextension = None

    # Check invalid file data
    if not submitsize:
        files.clear_temporary(userid)
        raise WeasylError("submitSizeZero")
    elif submitsize > 10 * _MEGABYTE:
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
    settings = []
    settings.append("f" if friends else "")
    settings.append(files.typeflag("submit", submitextension))
    settings.append(files.typeflag("cover", submitextension))
    settings = "".join(settings)

    # Insert submission data
    ch = define.meta.tables["character"]

    try:
        charid = define.engine.execute(ch.insert().returning(ch.c.charid), {
            "userid": userid,
            "unixtime": arrow.now(),
            "char_name": character.char_name,
            "age": character.age,
            "gender": character.gender,
            "height": character.height,
            "weight": character.weight,
            "species": character.species,
            "content": character.content,
            "rating": character.rating.code,
            "settings": settings,
        }).scalar()
    except PostgresError:
        files.clear_temporary(userid)
        raise

    # Assign search tags
    searchtag.associate(userid, tags, charid=charid)

    # Make submission file
    files.make_path(charid, "char")
    files.copy(tempsubmit, files.make_resource(userid, charid, "char/submit", submitextension))

    # Make cover file
    image.make_cover(tempsubmit, files.make_resource(userid, charid, "char/cover", submitextension))

    # Make thumbnail selection file
    if thumbsize:
        image.make_cover(
            tempthumb, files.make_resource(userid, charid, "char/.thumb"))

    thumbnail.create(userid, 0, 0, 0, 0, charid=charid, remove=False)

    # Create notifications
    welcome.character_insert(userid, charid, rating=character.rating.code,
                             settings=settings)

    # Clear temporary files
    files.clear_temporary(userid)

    define.metric('increment', 'characters')

    return charid


def reupload(userid, charid, submitdata):
    submitsize = len(submitdata)
    if not submitsize:
        raise WeasylError("submitSizeZero")
    elif submitsize > 10 * _MEGABYTE:
        raise WeasylError("submitSizeExceedsLimit")

    # Select character data
    query, = define.engine.execute("""
        SELECT userid, settings FROM character WHERE charid = %(character)s AND settings !~ 'h'
    """, character=charid)

    if userid != query.userid:
        raise WeasylError("Unexpected")

    im = image.from_string(submitdata)
    submitextension = image.image_extension(im)

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
    settings = re.sub(r'[~=].', '', query.settings)
    settings += files.typeflag("submit", submitextension)
    settings += files.typeflag("cover", submitextension)
    define.engine.execute("""
        UPDATE character
           SET settings = %(settings)s
         WHERE charid = %(character)s
    """, settings=settings, character=charid)


def is_hidden(charid):
    db = define.connect()
    ch = define.meta.tables['character']
    q = define.sa.select([ch.c.settings.op('~')('h')]).where(ch.c.charid == charid)
    results = db.execute(q).fetchall()
    return bool(results and results[0][0])


def select_view(userid, charid, rating, ignore=True, anyway=None):
    query = define.execute("""
        SELECT
            ch.userid, pr.username, ch.unixtime, ch.char_name, ch.age, ch.gender, ch.height, ch.weight, ch.species,
            ch.content, ch.rating, ch.settings, ch.page_views, pr.config
        FROM character ch
            INNER JOIN profile pr USING (userid)
        WHERE ch.charid = %i
    """, [charid], options=["single", "list"])

    if query and userid in staff.MODS and anyway == "true":
        pass
    elif not query or "h" in query[11]:
        raise WeasylError("characterRecordMissing")
    elif query[10] > rating and ((userid != query[0] and userid not in staff.MODS) or define.is_sfw_mode()):
        raise WeasylError("RatingExceeded")
    elif "f" in query[11] and not frienduser.check(userid, query[0]):
        raise WeasylError("FriendsOnly")
    elif ignore and ignoreuser.check(userid, query[0]):
        raise WeasylError("UserIgnored")
    elif ignore and blocktag.check(userid, charid=charid):
        raise WeasylError("TagBlocked")

    if define.common_view_content(userid, charid, "char"):
        query[12] += 1
    login = define.get_sysname(query[1])

    return {
        "charid": charid,
        "userid": query[0],
        "username": query[1],
        "user_media": media.get_user_media(query[0]),
        "mine": userid == query[0],
        "unixtime": query[2],
        "title": query[3],
        "age": query[4],
        "gender": query[5],
        "height": query[6],
        "weight": query[7],
        "species": query[8],
        "content": query[9],
        "rating": query[10],
        "settings": query[11],
        "reported": report.check(charid=charid),
        "favorited": favorite.check(userid, charid=charid),
        "page_views": query[12],
        "friends_only": "f" in query[11],
        "hidden_submission": "h" in query[11],
        "fave_count": favorite.count(charid=charid),
        "comments": comment.select(userid, charid=charid),
        "sub_media": fake_media_items(charid, query[0], login, query[11]),
        "tags": searchtag.select(charid=charid),
    }


def select_view_api(userid, charid, anyway=False, increment_views=False):
    query = define.execute("""
        SELECT
            ch.userid, pr.username, ch.unixtime, ch.char_name, ch.age, ch.gender, ch.height, ch.weight, ch.species,
            ch.content, ch.rating, ch.settings, ch.page_views, pr.config
        FROM character ch
            INNER JOIN profile pr USING (userid)
        WHERE ch.charid = %i
    """, [charid], options=["single", "list"])
    rating = define.get_rating(userid)

    if not query or 'h' in query[11]:
        raise WeasylError('characterRecordMissing')
    elif 'f' in query[11] and not frienduser.check(userid, query[0]):
        raise WeasylError('FriendsOnly')
    elif query[10] > rating and ((userid != query[0] and userid not in staff.MODS) or define.is_sfw_mode()):
        raise WeasylError('RatingExceeded')
    elif not anyway and ignoreuser.check(userid, query[0]):
        raise WeasylError('UserIgnored')
    elif not anyway and blocktag.check(userid, charid=charid):
        raise WeasylError('TagBlocked')

    if increment_views and define.common_view_content(userid, charid, 'char'):
        query[12] += 1
    login = define.get_sysname(query[1])

    return {
        "charid": charid,
        "owner": query[1],
        "owner_login": login,
        "owner_media": api.tidy_all_media(media.get_user_media(query[0])),
        "posted_at": define.iso8601(query[2]),
        "title": query[3],
        "age": query[4],
        "gender": query[5],
        "height": query[6],
        "weight": query[7],
        "species": query[8],
        "content": text.markdown(query[9]),
        "rating": query[10],
        "favorited": favorite.check(userid, charid=charid),
        "views": query[12],
        "friends_only": 'f' in query[11],
        "favorites": favorite.count(charid=charid),
        "comments": comment.count(charid=charid),
        "media": fake_media_items(charid, query[0], login, query[11], True),
        "tags": searchtag.select(charid=charid)
    }


def select_query(userid, rating, otherid=None, backid=None, nextid=None, options=[], config=None):

    statement = [" FROM character ch INNER JOIN profile pr ON ch.userid = pr.userid WHERE ch.settings !~ '[h]'"]

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
        statement.append(" AND ch.rating <= %i AND ch.settings !~ 'f'" % (rating,))

    # Content owner
    if otherid:
        statement.append(" AND ch.userid = %i" % (otherid,))

    # Browse selection
    if backid:
        statement.append(" AND ch.charid > %i" % (backid,))
    elif nextid:
        statement.append(" AND ch.charid < %i" % (nextid,))

    return statement


def select_count(userid, rating, otherid=None, backid=None, nextid=None, options=[], config=None):
    statement = ["SELECT count(ch.charid)"]
    statement.extend(select_query(userid, rating, otherid, backid, nextid,
                                  options, config))
    return define.execute("".join(statement))[0][0]


def select_list(userid, rating, limit, otherid=None, backid=None, nextid=None, options=[], config=None):
    statement = ["SELECT ch.charid, ch.char_name, ch.rating, ch.unixtime, ch.userid, pr.username, ch.settings "]
    statement.extend(select_query(userid, rating, otherid, backid, nextid,
                                  options, config))

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
    query = define.execute("SELECT userid, settings FROM character WHERE charid = %i",
                           [character.charid], options="single")

    if not query or "h" in query[1]:
        raise WeasylError("Unexpected")
    elif userid != query[0] and userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")
    elif not character.char_name:
        raise WeasylError("characterNameInvalid")
    elif not character.rating:
        raise WeasylError("Unexpected")
    profile.check_user_rating_allowed(userid, character.rating)

    # Assign settings
    settings = [query[1].replace("f", "")]
    settings.append("f" if friends_only else "")
    settings = "".join(settings)

    if "f" in settings:
        welcome.character_remove(character.charid)

    define.execute(
        """
            UPDATE character
            SET (char_name, age, gender, height, weight, species, content, rating, settings) =
                ('%s', '%s', '%s', '%s', '%s', '%s', '%s', %i, '%s')
            WHERE charid = %i
        """,
        [character.char_name, character.age, character.gender, character.height, character.weight, character.species,
         character.content, character.rating.code, settings, character.charid])

    if userid != query[0]:
        from weasyl import moderation
        moderation.note_about(
            userid, query[0], 'The following character was edited:',
            '- ' + text.markdown_link(character.char_name, '/character/%s?anyway=true' % (character.charid,)))


def remove(userid, charid):
    ownerid = define.get_ownerid(charid=charid)

    if userid not in staff.MODS and userid != ownerid:
        raise WeasylError("InsufficientPermissions")

    query = define.execute("UPDATE character SET settings = settings || 'h'"
                           " WHERE charid = %i AND settings !~ 'h'"
                           " RETURNING charid", [charid])

    if query:
        welcome.character_remove(charid)

    return ownerid


def fake_media_items(charid, userid, login, settings, absolutify=False):
    submission_url = define.cdnify_url(
        define.url_make(charid, "char/submit", query=[userid, settings], file_prefix=login))
    cover_url = define.cdnify_url(define.url_make(charid, "char/cover", query=[settings], file_prefix=login))
    thumbnail_url = define.cdnify_url(define.url_make(charid, "char/thumb", query=[settings]))

    if absolutify:
        submission_url = define.absolutify_url(submission_url)
        cover_url = define.absolutify_url(cover_url)
        thumbnail_url = define.absolutify_url(thumbnail_url)

    return {
        "submission": [{
            "display_url": submission_url,
            "described": {
                "cover": [{
                    "display_url": cover_url,
                }],
            },
        }],
        "thumbnail-generated": [{
            "display_url": thumbnail_url,
        }],
        "cover": [{
            "display_url": cover_url,
            "described": {
                "submission": [{
                    "display_url": submission_url,
                }],
            },
        }],
    }

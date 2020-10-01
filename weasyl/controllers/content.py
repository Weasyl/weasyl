from __future__ import absolute_import

import urlparse

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import ratings
from libweasyl import staff
from libweasyl.text import markdown, slug_for

from weasyl import (
    character, comment, define, folder, journal, macro, profile,
    report, searchtag, shout, submission, orm)
from weasyl.controllers.decorators import login_required, supports_json, token_checked
from weasyl.error import WeasylError
from weasyl.login import get_user_agent_id


# Content submission functions
@login_required
def submit_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "submit/submit.html", title="Submit Artwork"))


@login_required
def submit_visual_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")
    title = request.params.get('title', '')
    description = request.params.get('description', '')
    baseURL = request.params.get('baseURL', '')
    imageURL = request.params.get('imageURL', '')
    tags = request.params.getall('tags')
    if baseURL:
        imageURL = urlparse.urljoin(baseURL, imageURL)

    return Response(define.webpage(request.userid, "submit/visual.html", [
        # Folders
        folder.select_flat(request.userid),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 1000 <= i[0] < 2000],
        profile.get_user_ratings(request.userid),
        title, imageURL, tags, description
    ], title="Visual Artwork"))


@login_required
@token_checked
def submit_visual_post_(request):
    tags = searchtag.parse_tags(request.params.get('tags', ''))

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = request.params.get('title', '')
    s.rating = rating
    s.content = request.params.get('content', '')
    s.folderid = define.get_int(request.params.get('folderid', '')) or None
    s.subtype = define.get_int(request.params.get('subtype', ''))
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()
    thumbfile = request.params.get('thumbfile', u'')
    if thumbfile != u'':
        thumbfile = thumbfile.file.read()

    submitid = submission.create_visual(
        request.userid,
        s,
        friends_only=request.params.get('friends', ''),
        tags=tags,
        imageURL=request.params.get('imageURL', ''),
        thumbfile=thumbfile,
        submitfile=submitfile,
        critique=request.params.get('critique', False),
        create_notifications=('nonotification' not in request.params)
    )

    if 'customthumb' in request.params:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(s.title)))


@login_required
def submit_literary_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "submit/literary.html", [
        # Folders
        folder.select_flat(request.userid),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 2000 <= i[0] < 3000],
        profile.get_user_ratings(request.userid),
    ], title="Literary Artwork"))


@login_required
@token_checked
def submit_literary_post_(request):
    tags = searchtag.parse_tags(request.params.get('tags', ''))

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = request.params.get('title', '')
    s.rating = rating
    s.content = request.params.get('content', '')
    s.folderid = define.get_int(request.params.get('folderid', '')) or None
    s.subtype = define.get_int(request.params.get('subtype', ''))
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()
    thumbfile = request.params.get('thumbfile', u'')
    if thumbfile != u'':
        thumbfile = thumbfile.file.read()
    coverfile = request.params.get('coverfile', u'')
    if coverfile != u'':
        coverfile = coverfile.file.read()

    submitid, thumb = submission.create_literary(
        request.userid,
        s,
        embedlink=request.params.get('embedlink', ''),
        friends_only=request.params.get('friends', ''),
        tags=tags,
        coverfile=coverfile,
        thumbfile=thumbfile,
        submitfile=submitfile,
        critique=request.params.get('critique', False),
        create_notifications=('nonotification' not in request.params)
    )
    if thumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(s.title)))


@login_required
def submit_multimedia_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "submit/multimedia.html", [
        # Folders
        folder.select_flat(request.userid),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 3000 <= i[0] < 4000],
        profile.get_user_ratings(request.userid),
    ], title="Multimedia Artwork"))


@login_required
@token_checked
def submit_multimedia_post_(request):
    tags = searchtag.parse_tags(request.params.get('tags', ''))

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = request.params.get('title', '')
    s.rating = rating
    s.content = request.params.get('content', '')
    s.folderid = define.get_int(request.params.get('folderid', '')) or None
    s.subtype = define.get_int(request.params.get('subtype', ''))
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()
    thumbfile = request.params.get('thumbfile', u'')
    if thumbfile != u'':
        thumbfile = thumbfile.file.read()
    coverfile = request.params.get('coverfile', u'')
    if coverfile != u'':
        coverfile = coverfile.file.read()

    autothumb = ('noautothumb' not in request.params)

    submitid, thumb = submission.create_multimedia(
        request.userid,
        s,
        embedlink=request.params.get('embedlink', ''),
        friends_only=request.params.get('friends', ''),
        tags=tags,
        coverfile=coverfile,
        thumbfile=thumbfile,
        submitfile=submitfile,
        critique=request.params.get('critique', False),
        create_notifications=('nonotification' not in request.params),
        auto_thumb=autothumb)
    if thumb and not autothumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(s.title)))


@login_required
def submit_character_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "submit/character.html", [
        profile.get_user_ratings(request.userid),
    ], title="Character Profile"))


@login_required
@token_checked
def submit_character_post_(request):
    tags = searchtag.parse_tags(request.params.get('tags', ''))

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    c = orm.Character()
    c.age = request.params.get('age', '')
    c.gender = request.params.get('gender', '')
    c.height = request.params.get('height', '')
    c.weight = request.params.get('weight', '')
    c.species = request.params.get('species', '')
    c.char_name = request.params.get('title', '')
    c.content = request.params.get('content', '')
    c.rating = rating

    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()
    thumbfile = request.params.get('thumbfile', u'')
    if thumbfile != u'':
        thumbfile = thumbfile.file.read()

    charid = character.create(request.userid, c, request.params.get('friends', ''), tags,
                              thumbfile, submitfile)
    raise HTTPSeeOther(location="/manage/thumbnail?charid=%i" % (charid,))


@login_required
def submit_journal_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "submit/journal.html",
                                   [profile.get_user_ratings(request.userid)], title="Journal Entry"))


@login_required
@token_checked
def submit_journal_post_(request):
    tags = searchtag.parse_tags(request.params.get('tags', ''))

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.title = request.params.get('title', '')
    j.rating = rating
    j.content = request.params.get('content', '')
    j.submitter_ip_address = request.client_addr
    j.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)
    journalid = journal.create(request.userid, j, request.params.get('friends', ''),
                               tags=tags)
    raise HTTPSeeOther(location="/journal/%i/%s" % (journalid, slug_for(j.title)))


@login_required
@token_checked
@supports_json
def submit_shout_(request):
    staffnotes = int(request.params.get('staffnotes', 0))

    if staffnotes and request.userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    commentid = shout.insert(
        request.userid,
        target_user=define.get_int(request.params.get('userid', '') or staffnotes),
        parentid=define.get_int(request.params.get('parentid', '')),
        content=request.params.get('content', ''),
        staffnotes=bool(staffnotes),
    )

    if request.params.get('format', '') == "json":
        return {"id": commentid}

    if staffnotes:
        raise HTTPSeeOther(location='/staffnotes?userid=%i#cid%i' % (define.get_int(staffnotes), commentid))
    else:
        raise HTTPSeeOther(location="/shouts?userid=%i#cid%i" % (c.userid, commentid))


@login_required
@token_checked
@supports_json
def submit_comment_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    submitid = define.get_int(request.params.get('submitid', ''))
    charid = define.get_int(request.params.get('charid', ''))
    journalid = define.get_int(request.params.get('journalid', ''))
    updateid = define.get_int(request.params.get('updateid', ''))
    parentid = define.get_int(request.params.get('updateid', ''))
    content = request.params.get('content', '')

    commentid = comment.insert(request.userid, charid=charid,
                               parentid=parentid,
                               submitid=submitid,
                               journalid=journalid,
                               updateid=updateid,
                               content=content)

    if request.params.get('format', '') == "json":
        return {
            "id": commentid,
            "html": markdown(content)
        }

    if submitid:
        raise HTTPSeeOther(location="/submission/%i#cid%i" % (submitid, commentid))
    elif charid:
        raise HTTPSeeOther(location="/character/%i#cid%i" % (charid, commentid))
    elif journalid:
        raise HTTPSeeOther(location="/journal/%i#cid%i" % (journalid, commentid))
    elif updateid:
        raise HTTPSeeOther(location="/site-updates/%i#cid%i" % (updateid, commentid))
    else:
        raise WeasylError("Unexpected")


@login_required
@token_checked
def submit_report_(request):
    submitid = request.params.get('submitid', '')
    charid = request.params.get('charid', '')
    journalid = request.params.get('journalid', '')
    reportid = request.params.get('reportid', '')
    violation = request.params.get('violation', '')
    content = request.params.get('content', '')

    report.create(request.userid, submitid, charid, journalid, violation, content)
    if reportid:
        raise HTTPSeeOther(location="/modcontrol/report?reportid=%s" % (reportid,))
    elif define.get_int(submitid):
        raise HTTPSeeOther(location="/submission/%i" % (define.get_int(submitid),))
    elif define.get_int(charid):
        raise HTTPSeeOther(location="/character/%i" % (define.get_int(charid),))
    else:
        raise HTTPSeeOther(location="/journal/%i" % (define.get_int(journalid),))


@login_required
@token_checked
def submit_tags_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    tags = searchtag.parse_tags(request.params.get('tags', ''))

    submitid = define.get_int(request.params.get('submitid', ''))
    charid = define.get_int(request.params.get('charid', ''))
    journalid = define.get_int(request.params.get('journalid', ''))
    preferred_tags_userid = define.get_int(request.params.get('preferred_tags_userid', ''))
    optout_tags_userid = define.get_int(request.params.get('optout_tags_userid', ''))

    result = searchtag.associate(request.userid, tags, submitid, charid, journalid, preferred_tags_userid, optout_tags_userid)
    if result:
        failed_tag_message = ""
        if result["add_failure_restricted_tags"] is not None:
            failed_tag_message += "The following tags have been restricted from being added to this item by the content owner, or Weasyl staff: **" + result["add_failure_restricted_tags"] + "**. \n"
        if result["remove_failure_owner_set_tags"] is not None:
            failed_tag_message += "The following tags were not removed from this item as the tag was added by the owner: **" + result["remove_failure_owner_set_tags"] + "**.\n"
        failed_tag_message += "Any other changes to this item's tags were completed."
    if submitid:
        location = "/submission/%i" % (submitid,)
        if not result:
            raise HTTPSeeOther(location=location)
        else:
            return Response(define.errorpage(request.userid, failed_tag_message,
                                             [["Return to Content", location]]))
    elif charid:
        location = "/character/%i" % (charid,)
        if not result:
            raise HTTPSeeOther(location=location)
        else:
            return Response(define.errorpage(request.userid, failed_tag_message,
                                             [["Return to Content", location]]))
    elif journalid:
        location = "/journal/%i" % (journalid,)
        if not result:
            raise HTTPSeeOther(location=location)
        else:
            return Response(define.errorpage(request.userid, failed_tag_message,
                                             [["Return to Content", location]]))
    else:
        raise HTTPSeeOther(location="/control/editcommissionsettings")


@login_required
def reupload_submission_get_(request):
    submitid = define.get_int(request.params.get('submitid', ''))

    if request.userid != define.get_ownerid(submitid=submitid):
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "submit/reupload_submission.html", [
        "submission",
        # SubmitID
        submitid,
    ], title="Reupload Submission"))


@login_required
@token_checked
def reupload_submission_post_(request):
    targetid = define.get_int(request.params.get('targetid', ''))
    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()

    if request.userid != define.get_ownerid(submitid=targetid):
        raise WeasylError('InsufficientPermissions')

    submission.reupload(request.userid, targetid, submitfile)
    raise HTTPSeeOther(location="/submission/%i" % (targetid,))


@login_required
def reupload_character_get_(request):
    charid = define.get_int(request.params.get('charid', ''))

    if request.userid != define.get_ownerid(charid=charid):
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "submit/reupload_submission.html", [
        "character",
        # charid
        charid,
    ], title="Reupload Character Image"))


@login_required
@token_checked
def reupload_character_post_(request):
    targetid = define.get_int(request.params.get('targetid', ''))
    submitfile = request.params.get('submitfile', u'')
    if submitfile != u'':
        submitfile = submitfile.file.read()

    if request.userid != define.get_ownerid(charid=targetid):
        raise WeasylError('InsufficientPermissions')

    character.reupload(request.userid, targetid, submitfile)
    raise HTTPSeeOther(location="/character/%i" % (targetid,))


@login_required
def reupload_cover_get_(request):
    submitid = define.get_int(request.params.get('submitid', ''))

    if request.userid != define.get_ownerid(submitid=submitid):
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "submit/reupload_cover.html", [submitid], title="Reupload Cover Artwork"))


@login_required
@token_checked
def reupload_cover_post_(request):
    submitid = define.get_int(request.params.get('submitid', ''))

    coverfile = request.params.get('coverfile', u'')
    if coverfile != u'':
        coverfile = coverfile.file.read()

    submission.reupload_cover(request.userid, submitid, coverfile)
    raise HTTPSeeOther(location="/submission/%i" % (submitid,))


# Content editing functions
@login_required
def edit_submission_get_(request):
    detail = submission.select_view(
        request.userid,
        define.get_int(request.params.get('submitid', '')),
        ratings.EXPLICIT.code,
        False,
        anyway=request.params.get('anyway', '')
    )

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')

    submission_category = detail['subtype'] // 1000 * 1000

    return Response(define.webpage(request.userid, "edit/submission.html", [
        # Submission detail
        detail,
        # Folders
        folder.select_flat(detail['userid']),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST
         if submission_category <= i[0] < submission_category + 1000],
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Submission"))


@login_required
@token_checked
def edit_submission_post_(request):
    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.submitid = define.get_int(request.params.get('submitid', ''))
    s.title = request.params.get('title', '')
    s.rating = rating
    s.content = request.params.get('content', '')
    s.folderid = define.get_int(request.params.get('folderid', '')) or None
    s.subtype = define.get_int(request.params.get('subtype', ''))

    submission.edit(
        request.userid,
        s,
        embedlink=request.params.get('embedlink', ''),
        friends_only=request.params.get('friends', False),
        critique=request.params.get('critique', False)
    )
    raise HTTPSeeOther(location="/submission/%i/%s%s" % (
        define.get_int(s.submitid),
        slug_for(s.title),
        "?anyway=true" if request.userid in staff.MODS else ''
    ))


@login_required
def edit_character_get_(request):
    detail = character.select_view(
        request.userid,
        define.get_int(request.params.get('charid')),
        ratings.EXPLICIT.code,
        False,
        anyway=request.params.get('anyway', '')
    )

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "edit/character.html", [
        # Submission detail
        detail,
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Character"))


@login_required
@token_checked
def edit_character_post_(request):
    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    c = orm.Character()
    c.charid = define.get_int(request.params.get('charid'))
    c.age = request.params.get('age', '')
    c.gender = request.params.get('gender', '')
    c.height = request.params.get('height', '')
    c.weight = request.params.get('weight', '')
    c.species = request.params.get('species', '')
    c.char_name = request.params.get('title', '')
    c.content = request.params.get('content', '')
    c.rating = rating

    character.edit(request.userid, c, friends_only=request.params.get('friends', False))
    raise HTTPSeeOther(location="/character/%i/%s%s" % (
        define.get_int(c.charid),
        slug_for(c.char_name),
        ("?anyway=true" if request.userid in staff.MODS else '')
    ))


@login_required
def edit_journal_get_(request):
    journalid = define.get_int(request.params.get('journalid', ''))

    detail = journal.select_view(request.userid, ratings.EXPLICIT.code, journalid, False, anyway=request.params.get('anyway', ''))

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        raise WeasylError('InsufficientPermissions')

    return Response(define.webpage(request.userid, "edit/journal.html", [
        # Journal detail
        detail,
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Journal"))


@login_required
@token_checked
def edit_journal_post_(request):
    rating = ratings.CODE_MAP.get(define.get_int(request.params.get('rating', '')))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.journalid = define.get_int(request.params.get('journalid', ''))
    j.title = request.params.get('title', '')
    j.rating = rating
    j.content = request.params.get('content', '')
    journal.edit(request.userid, j, friends_only=request.params.get('friends', False))
    raise HTTPSeeOther(location="/journal/%i/%s%s" % (
        define.get_int(j.journalid),
        slug_for(j.title),
        ("?anyway=true" if request.userid in staff.MODS else '')
    ))


# Content removal functions
@login_required
@token_checked
def remove_submission_(request):
    ownerid = submission.remove(request.userid, define.get_int(request.params.get('submitid', '')))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/submissions?userid=%i" % (ownerid,))


@login_required
@token_checked
def remove_character_(request):
    ownerid = character.remove(request.userid, define.get_int(request.params.get('charid', '')))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/characters?userid=%i" % (ownerid,))


@login_required
@token_checked
def remove_journal_(request):
    ownerid = journal.remove(request.userid, define.get_int(request.params.get('journalid', '')))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/journals?userid=%i" % (ownerid,))


@login_required
@token_checked
@supports_json
def remove_comment_(request):
    commentid = define.get_int(request.params.get('commentid', ''))
    feature = request.params.get('feature', '')

    if feature == "userid":
        targetid = shout.remove(request.userid, commentid=commentid)
    else:
        targetid = comment.remove(request.userid, commentid=commentid, feature=feature)

    if request.params.get('format', '') == "json":
        return {"success": True}

    if feature == "userid":
        raise HTTPSeeOther(location="/shouts?userid=%i" % (targetid,))
    elif feature == "submit":
        raise HTTPSeeOther(location="/submission/%i" % (targetid,))
    elif feature == "char":
        raise HTTPSeeOther(location="/character/%i" % (targetid,))
    elif feature == "journal":
        raise HTTPSeeOther(location="/journal/%i" % (targetid,))

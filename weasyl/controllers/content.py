from __future__ import absolute_import

import urlparse

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import ratings
from libweasyl import staff
from libweasyl.text import slug_for

from weasyl import (
    character, comment, define, errorcode, folder, journal, macro, profile,
    report, searchtag, shout, submission, orm)
from weasyl.controllers.decorators import login_required, supports_json, token_checked
from weasyl.error import WeasylError


# Content submission functions
@login_required
def submit_(request):
    return Response(define.webpage(request.userid, "submit/submit.html", title="Submit Artwork"))


@login_required
def submit_visual_get_(request):
    form = request.web_input(title='', tags=[], description='', imageURL='', baseURL='')
    if form.baseURL:
        form.imageURL = urlparse.urljoin(form.baseURL, form.imageURL)

    return Response(define.webpage(request.userid, "submit/visual.html", [
        # Folders
        folder.select_list(request.userid, "drop/all"),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 1000 <= i[0] < 2000],
        profile.get_user_ratings(request.userid),
        form,
    ], title="Visual Artwork"))


@login_required
@token_checked
def submit_visual_post_(request):
    form = request.web_input(submitfile="", thumbfile="", title="", folderid="",
                             subtype="", rating="", friends="", critique="", content="",
                             tags="", imageURL="")

    tags = searchtag.parse_tags(form.tags)

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)

    submitid = submission.create_visual(
        request.userid, s, friends_only=form.friends, tags=tags,
        imageURL=form.imageURL, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique=form.critique, create_notifications=('nonotification' not in form))

    if 'customthumb' in form:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


@login_required
def submit_literary_get_(request):
    return Response(define.webpage(request.userid, "submit/literary.html", [
        # Folders
        folder.select_list(request.userid, "drop/all"),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 2000 <= i[0] < 3000],
        profile.get_user_ratings(request.userid),
    ], title="Literary Artwork"))


@login_required
@token_checked
def submit_literary_post_(request):
    form = request.web_input(submitfile="", coverfile="boop", thumbfile="", title="",
                             folderid="", subtype="", rating="", friends="", critique="",
                             content="", tags="", embedlink="")

    tags = searchtag.parse_tags(form.tags)

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)

    submitid, thumb = submission.create_literary(
        request.userid, s, embedlink=form.embedlink, friends_only=form.friends, tags=tags,
        coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique=form.critique, create_notifications=('nonotification' not in form))
    if thumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


@login_required
def submit_multimedia_get_(request):
    return Response(define.webpage(request.userid, "submit/multimedia.html", [
        # Folders
        folder.select_list(request.userid, "drop/all"),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 3000 <= i[0] < 4000],
        profile.get_user_ratings(request.userid),
    ], title="Multimedia Artwork"))


@login_required
@token_checked
def submit_multimedia_post_(request):
    form = request.web_input(submitfile="", coverfile="", thumbfile="", embedlink="",
                             title="", folderid="", subtype="", rating="", friends="",
                             critique="", content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)

    autothumb = ('noautothumb' not in form)

    submitid, thumb = submission.create_multimedia(
        request.userid, s, embedlink=form.embedlink, friends_only=form.friends, tags=tags,
        coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique=form.critique, create_notifications=('nonotification' not in form),
        auto_thumb=autothumb)
    if thumb and not autothumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


@login_required
def submit_character_get_(request):
    return Response(define.webpage(request.userid, "submit/character.html", [
        profile.get_user_ratings(request.userid),
    ], title="Character Profile"))


@login_required
@token_checked
def submit_character_post_(request):
    form = request.web_input(submitfile="", thumbfile="", title="", age="", gender="",
                             height="", weight="", species="", rating="", friends="",
                             content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    c = orm.Character()
    c.age = form.age
    c.gender = form.gender
    c.height = form.height
    c.weight = form.weight
    c.species = form.species
    c.char_name = form.title
    c.content = form.content
    c.rating = rating

    charid = character.create(request.userid, c, form.friends, tags,
                              form.thumbfile, form.submitfile)
    raise HTTPSeeOther(location="/manage/thumbnail?charid=%i" % (charid,))


@login_required
def submit_journal_get_(request):
    return Response(define.webpage(request.userid, "submit/journal.html",
                                   [profile.get_user_ratings(request.userid)], title="Journal Entry"))


@login_required
@token_checked
def submit_journal_post_(request):
    form = request.web_input(title="", rating="", friends="", members="", content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not define.config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.title = form.title
    j.rating = rating
    j.content = form.content
    journalid = journal.create(request.userid, j, friends_only=form.friends,
                               tags=tags)
    raise HTTPSeeOther(location="/journal/%i/%s" % (journalid, slug_for(form.title)))


@login_required
@token_checked
@supports_json
def submit_shout_(request):
    form = request.web_input(userid="", parentid="", content="", staffnotes="", format="")

    if form.staffnotes and request.userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    c = orm.Comment()
    c.parentid = define.get_int(form.parentid)
    c.userid = define.get_int(form.userid or form.staffnotes)
    c.content = form.content

    commentid = shout.insert(request.userid, c, staffnotes=form.staffnotes)

    if form.format == "json":
        return {"id": commentid}

    if form.staffnotes:
        raise HTTPSeeOther(location='/staffnotes?userid=%i#cid%i' % (define.get_int(form.staffnotes), commentid))
    else:
        raise HTTPSeeOther(location="/shouts?userid=%i#cid%i" % (define.get_int(form.userid), commentid))


@login_required
@token_checked
@supports_json
def submit_comment_(request):
    form = request.web_input(submitid="", charid="", journalid="", parentid="", content="", format="")

    commentid = comment.insert(request.userid, charid=define.get_int(form.charid),
                               parentid=define.get_int(form.parentid),
                               submitid=define.get_int(form.submitid),
                               journalid=define.get_int(form.journalid),
                               content=form.content)

    if form.format == "json":
        return {"id": commentid}

    if define.get_int(form.submitid):
        raise HTTPSeeOther(location="/submission/%i#cid%i" % (define.get_int(form.submitid), commentid))
    elif define.get_int(form.charid):
        raise HTTPSeeOther(location="/character/%i#cid%i" % (define.get_int(form.charid), commentid))
    else:
        raise HTTPSeeOther(location="/journal/%i#cid%i" % (define.get_int(form.journalid), commentid))


@login_required
@token_checked
def submit_report_(request):
    form = request.web_input(submitid="", charid="", journalid="", reportid="", violation="", content="")

    report.create(request.userid, form)
    if form.reportid:
        raise HTTPSeeOther(location="/modcontrol/report?reportid=%s" % (form.reportid,))
    elif define.get_int(form.submitid):
        raise HTTPSeeOther(location="/submission/%i" % (define.get_int(form.submitid),))
    elif define.get_int(form.charid):
        raise HTTPSeeOther(location="/character/%i" % (define.get_int(form.charid),))
    else:
        raise HTTPSeeOther(location="/journal/%i" % (define.get_int(form.journalid),))


@login_required
@token_checked
def submit_tags_(request):
    form = request.web_input(submitid="", charid="", journalid="", preferred_tags_userid="", optout_tags_userid="", tags="")

    tags = searchtag.parse_tags(form.tags)

    submitid = define.get_int(form.submitid)
    charid = define.get_int(form.charid)
    journalid = define.get_int(form.journalid)
    preferred_tags_userid = define.get_int(form.preferred_tags_userid)
    optout_tags_userid = define.get_int(form.optout_tags_userid)

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
    form = request.web_input(submitid="")
    form.submitid = define.get_int(form.submitid)

    if request.userid != define.get_ownerid(submitid=form.submitid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "submit/reupload_submission.html", [
        "submission",
        # SubmitID
        form.submitid,
    ], title="Reupload Submission"))


@login_required
@token_checked
def reupload_submission_post_(request):
    form = request.web_input(targetid="", submitfile="")
    form.targetid = define.get_int(form.targetid)

    if request.userid != define.get_ownerid(submitid=form.targetid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    submission.reupload(request.userid, form.targetid, form.submitfile)
    raise HTTPSeeOther(location="/submission/%i" % (form.targetid,))


@login_required
def reupload_character_get_(request):
    form = request.web_input(charid="")
    form.charid = define.get_int(form.charid)

    if request.userid != define.get_ownerid(charid=form.charid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "submit/reupload_submission.html", [
        "character",
        # charid
        form.charid,
    ], title="Reupload Character Image"))


@login_required
@token_checked
def reupload_character_post_(request):
    form = request.web_input(targetid="", submitfile="")
    form.targetid = define.get_int(form.targetid)

    if request.userid != define.get_ownerid(charid=form.targetid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    character.reupload(request.userid, form.targetid, form.submitfile)
    raise HTTPSeeOther(location="/character/%i" % (form.targetid,))


@login_required
def reupload_cover_get_(request):
    form = request.web_input(submitid="")
    form.submitid = define.get_int(form.submitid)

    if request.userid != define.get_ownerid(submitid=form.submitid):
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "submit/reupload_cover.html", [form.submitid], title="Reupload Cover Artwork"))


@login_required
@token_checked
def reupload_cover_post_(request):
    form = request.web_input(submitid="", coverfile="")
    form.submitid = define.get_int(form.submitid)

    submission.reupload_cover(request.userid, form.submitid, form.coverfile)
    raise HTTPSeeOther(location="/submission/%i" % (form.submitid,))


# Content editing functions
@login_required
def edit_submission_get_(request):
    form = request.web_input(submitid="", anyway="")
    form.submitid = define.get_int(form.submitid)

    detail = submission.select_view(request.userid, form.submitid, ratings.EXPLICIT.code, False, anyway=form.anyway)

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        return Response(define.errorpage(request.userid, errorcode.permission))

    submission_category = detail['subtype'] // 1000 * 1000

    return Response(define.webpage(request.userid, "edit/submission.html", [
        # Submission detail
        detail,
        # Folders
        folder.select_list(detail['userid'], "drop/all"),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST
         if submission_category <= i[0] < submission_category + 1000],
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Submission"))


@login_required
@token_checked
def edit_submission_post_(request):
    form = request.web_input(submitid="", title="", folderid="", subtype="", rating="",
                             content="", friends="", critique="", embedlink="")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.submitid = define.get_int(form.submitid)
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)

    submission.edit(request.userid, s, embedlink=form.embedlink,
                    friends_only=form.friends, critique=form.critique)
    raise HTTPSeeOther(location="/submission/%i/%s%s" % (
        define.get_int(form.submitid),
        slug_for(form.title),
        "?anyway=true" if request.userid in staff.MODS else ''
    ))


@login_required
def edit_character_get_(request):
    form = request.web_input(charid="", anyway="")
    form.charid = define.get_int(form.charid)

    detail = character.select_view(request.userid, form.charid, ratings.EXPLICIT.code, False, anyway=form.anyway)

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "edit/character.html", [
        # Submission detail
        detail,
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Character"))


@login_required
@token_checked
def edit_character_post_(request):
    form = request.web_input(charid="", title="", age="", gender="", height="",
                             weight="", species="", rating="", content="", friends="")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    c = orm.Character()
    c.charid = define.get_int(form.charid)
    c.age = form.age
    c.gender = form.gender
    c.height = form.height
    c.weight = form.weight
    c.species = form.species
    c.char_name = form.title
    c.content = form.content
    c.rating = rating

    character.edit(request.userid, c, friends_only=form.friends)
    raise HTTPSeeOther(location="/character/%i/%s%s" % (
        define.get_int(form.charid),
        slug_for(form.title),
        ("?anyway=true" if request.userid in staff.MODS else '')
    ))


@login_required
def edit_journal_get_(request):
    form = request.web_input(journalid="", anyway="")
    form.journalid = define.get_int(form.journalid)

    detail = journal.select_view(request.userid, ratings.EXPLICIT.code, form.journalid, False, anyway=form.anyway)

    if request.userid != detail['userid'] and request.userid not in staff.MODS:
        return Response(define.errorpage(request.userid, errorcode.permission))

    return Response(define.webpage(request.userid, "edit/journal.html", [
        # Journal detail
        detail,
        profile.get_user_ratings(detail['userid']),
    ], title="Edit Journal"))


@login_required
@token_checked
def edit_journal_post_(request):
    form = request.web_input(journalid="", title="", rating="", friends="", content="")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.journalid = define.get_int(form.journalid)
    j.title = form.title
    j.rating = rating
    j.content = form.content
    journal.edit(request.userid, j, friends_only=form.friends)
    raise HTTPSeeOther(location="/journal/%i/%s%s" % (
        define.get_int(form.journalid),
        slug_for(form.title),
        ("?anyway=true" if request.userid in staff.MODS else '')
    ))


# Content removal functions
@login_required
@token_checked
def remove_submission_(request):
    form = request.web_input(submitid="")

    ownerid = submission.remove(request.userid, define.get_int(form.submitid))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/submissions?userid=%i" % (ownerid,))


@login_required
@token_checked
def remove_character_(request):
    form = request.web_input(charid="")

    ownerid = character.remove(request.userid, define.get_int(form.charid))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/characters?userid=%i" % (ownerid,))


@login_required
@token_checked
def remove_journal_(request):
    form = request.web_input(journalid="")

    ownerid = journal.remove(request.userid, define.get_int(form.journalid))
    if request.userid == ownerid:
        raise HTTPSeeOther(location="/control")  # todo
    else:
        raise HTTPSeeOther(location="/journals?userid=%i" % (ownerid,))


@login_required
@token_checked
@supports_json
def remove_comment_(request):
    form = request.web_input(commentid="", feature="", format="")
    commentid = define.get_int(form.commentid)

    if form.feature == "userid":
        targetid = shout.remove(request.userid, commentid=commentid)
    else:
        targetid = comment.remove(request.userid, commentid=commentid, feature=form.feature)

    if form.format == "json":
        return {"success": True}

    if form.feature == "userid":
        raise HTTPSeeOther(location="/shouts?userid=%i" % (targetid,))
    elif form.feature == "submit":
        raise HTTPSeeOther(location="/submission/%i" % (targetid,))
    elif form.feature == "char":
        raise HTTPSeeOther(location="/character/%i" % (targetid,))
    elif form.feature == "journal":
        raise HTTPSeeOther(location="/journal/%i" % (targetid,))

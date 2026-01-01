from urllib.parse import urljoin

from pyramid.httpexceptions import HTTPConflict
from pyramid.httpexceptions import HTTPNoContent
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from libweasyl import ratings
from libweasyl import staff
from libweasyl.text import markdown, slug_for

from weasyl import (
    character, comment, define, folder, journal, macro, profile,
    report, searchtag, shout, submission, orm)
from weasyl.config import config_read_bool
from weasyl.controllers.decorators import login_required, supports_json, token_checked
from weasyl.error import WeasylError
from weasyl.forms import expect_id
from weasyl.forms import expect_tag
from weasyl.forms import only
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

    form = request.web_input(title='', tags=[], description='', imageURL='', baseURL='')
    if form.baseURL:
        form.imageURL = urljoin(form.baseURL, form.imageURL)

    return Response(define.webpage(request.userid, "submit/visual.html", [
        # Folders
        folder.select_flat(request.userid),
        # Subtypes
        [i for i in macro.MACRO_SUBCAT_LIST if 1000 <= i[0] < 2000],
        profile.get_user_ratings(request.userid),
        form,
    ], title="Visual Artwork"))


@login_required
@token_checked
def submit_visual_post_(request):
    form = request.web_input(submitfile="", thumbfile="", title="", folderid="",
                             subtype="", rating="", content="",
                             tags="", imageURL="")

    tags = searchtag.parse_tags(form.tags)

    if not config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    submitid = submission.create_visual(
        request.userid, s, friends_only='friends' in request.POST, tags=tags,
        imageURL=form.imageURL, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique='critique' in request.POST, create_notifications=('nonotification' not in form))

    if 'customthumb' in form:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


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
    form = request.web_input(submitfile="", coverfile="", thumbfile="", title="",
                             folderid="", subtype="", rating="",
                             content="", tags="", embedlink="")

    tags = searchtag.parse_tags(form.tags)

    if not config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    submitid, thumb = submission.create_literary(
        request.userid, s, embedlink=form.embedlink, friends_only='friends' in request.POST, tags=tags,
        coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique='critique' in request.POST, create_notifications=('nonotification' not in form))
    if thumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


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
    form = request.web_input(submitfile="", coverfile="", thumbfile="", embedlink="",
                             title="", folderid="", subtype="", rating="",
                             content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    s = orm.Submission()
    s.title = form.title
    s.rating = rating
    s.content = form.content
    s.folderid = define.get_int(form.folderid) or None
    s.subtype = define.get_int(form.subtype)
    s.submitter_ip_address = request.client_addr
    s.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)

    autothumb = ('noautothumb' not in form)

    submitid, thumb = submission.create_multimedia(
        request.userid, s, embedlink=form.embedlink, friends_only='friends' in request.POST, tags=tags,
        coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
        critique='critique' in request.POST, create_notifications=('nonotification' not in form),
        auto_thumb=autothumb)
    if thumb and not autothumb:
        raise HTTPSeeOther(location="/manage/thumbnail?submitid=%i" % (submitid,))
    else:
        raise HTTPSeeOther(location="/submission/%i/%s" % (submitid, slug_for(form.title)))


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
    form = request.web_input(submitfile="", thumbfile="", title="", age="", gender="",
                             height="", weight="", species="", rating="",
                             content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

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

    charid = character.create(
        request.userid, c,
        friends_only='friends' in request.POST,
        tags=tags,
        thumbfile=form.thumbfile,
        submitfile=form.submitfile,
    )
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
    form = request.web_input(title="", rating="", members="", content="", tags="")

    tags = searchtag.parse_tags(form.tags)

    if not config_read_bool("allow_submit"):
        raise WeasylError("FeatureDisabled")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.title = form.title
    j.rating = rating
    j.content = form.content
    j.submitter_ip_address = request.client_addr
    j.submitter_user_agent_id = get_user_agent_id(ua_string=request.user_agent)
    journalid = journal.create(request.userid, j, friends_only='friends' in request.POST,
                               tags=tags)
    raise HTTPSeeOther(location="/journal/%i/%s" % (journalid, slug_for(form.title)))


@login_required
@token_checked
@supports_json
def submit_shout_(request):
    form = request.web_input(userid="", parentid="", content="", staffnotes="", format="")

    if form.staffnotes and request.userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    commentid = shout.insert(
        request.userid,
        target_user=define.get_int(form.userid or form.staffnotes),
        parentid=define.get_int(form.parentid),
        content=form.content,
        staffnotes=bool(form.staffnotes),
    )

    if form.format == "json":
        return {
            "id": commentid,
            "html": markdown(form.content),
        }

    if form.staffnotes:
        raise HTTPSeeOther(location='/staffnotes?userid=%i#cid%i' % (define.get_int(form.staffnotes), commentid))
    else:
        raise HTTPSeeOther(location="/shouts?userid=%i#cid%i" % (define.get_int(form.userid), commentid))


@login_required
@token_checked
@supports_json
def submit_comment_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(submitid="", charid="", journalid="", updateid="", parentid="", content="", format="")
    updateid = define.get_int(form.updateid)

    commentid = comment.insert(request.userid, charid=define.get_int(form.charid),
                               parentid=define.get_int(form.parentid),
                               submitid=define.get_int(form.submitid),
                               journalid=define.get_int(form.journalid),
                               updateid=updateid,
                               content=form.content)

    if form.format == "json":
        return {
            "id": commentid,
            "html": markdown(form.content),
        }

    if define.get_int(form.submitid):
        raise HTTPSeeOther(location="/submission/%i#cid%i" % (define.get_int(form.submitid), commentid))
    elif define.get_int(form.charid):
        raise HTTPSeeOther(location="/character/%i#cid%i" % (define.get_int(form.charid), commentid))
    elif define.get_int(form.journalid):
        raise HTTPSeeOther(location="/journal/%i#cid%i" % (define.get_int(form.journalid), commentid))
    elif updateid:
        raise HTTPSeeOther(location="/site-updates/%i#cid%i" % (updateid, commentid))
    else:
        raise WeasylError("Unexpected")


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
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    target_key, targetid = only(
        (key, expect_id(request.POST[key]))
        for key in (
            "submitid",
            "charid",
            "journalid",
        )
        if key in request.POST
    )
    tags = searchtag.parse_tags(request.POST["tags"])

    match target_key:
        case "submitid":
            target = searchtag.SubmissionTarget(targetid)
        case "charid":
            target = searchtag.CharacterTarget(targetid)
        case "journalid":
            target = searchtag.JournalTarget(targetid)
        case _:
            assert False

    restricted_tags = searchtag.associate(
        userid=request.userid,
        target=target,
        tag_names=tags,
    )

    location = f"/{target.path_component}/{target.id}"

    if restricted_tags:
        failed_tag_message = (
            f"The following tags have been restricted from being added to this item by the content owner, or Weasyl staff: **{' '.join(restricted_tags)}**. \n"
            "Any other changes to this item's tags were completed."
        )
        return Response(define.errorpage(request.userid, failed_tag_message,
                                         [("Return to Content", location)]))

    raise HTTPSeeOther(location=location)


@login_required
@token_checked
def tag_status_put(request):
    feature = request.matchdict["feature"]
    targetid = expect_id(request.matchdict["targetid"])
    tag_name = expect_tag(request.matchdict["tag"])

    target = searchtag.get_target(feature, targetid)

    match request.body:
        case b"approve":
            action = searchtag.SuggestionAction.APPROVE
        case b"reject":
            action = searchtag.SuggestionAction.REJECT
        case _:
            raise WeasylError("Unexpected")

    result = searchtag.suggestion_arbitrate(
        userid=request.userid,
        target=target,
        tag_name=tag_name,
        action=action,
    )

    match result:
        case searchtag.SuggestionActionFailure():
            return HTTPConflict(b"\x00")
        case searchtag.SuggestionActionSuccess():
            return Response(b"\x01" + (result.undo_token or b""))


@login_required
@token_checked
def tag_status_delete(request):
    feature = request.matchdict["feature"]
    targetid = expect_id(request.matchdict["targetid"])
    tag_name = expect_tag(request.matchdict["tag"])

    target = searchtag.get_target(feature, targetid)

    try:
        searchtag.suggestion_action_undo(
            userid=request.userid,
            target=target,
            tag_name=tag_name,
            undo_token=request.body,
        )
    except searchtag.UndoExpired:
        return HTTPConflict()

    return HTTPNoContent()


@login_required
@token_checked
def tag_feedback_put(request):
    feature = request.matchdict["feature"]
    targetid = expect_id(request.matchdict["targetid"])
    tag_name = expect_tag(request.matchdict["tag"])
    reasons = request.POST.getall("reason")

    target = searchtag.get_target(feature, targetid)

    searchtag.set_tag_feedback(
        userid=request.userid,
        target=target,
        tag_name=tag_name,
        feedback=searchtag.SuggestionFeedback(
            incorrect="incorrect" in reasons,
            unwanted="unwanted" in reasons,
            abusive="abusive" in reasons,
        ),
    )

    return HTTPNoContent()


@login_required
def reupload_submission_get_(request):
    form = request.web_input(submitid="")
    form.submitid = define.get_int(form.submitid)

    if request.userid != define.get_ownerid(submitid=form.submitid):
        raise WeasylError('InsufficientPermissions')

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

    submission.reupload(request.userid, form.targetid, form.submitfile)
    raise HTTPSeeOther(location="/submission/%i" % (form.targetid,))


@login_required
def reupload_character_get_(request):
    form = request.web_input(charid="")
    form.charid = define.get_int(form.charid)

    if request.userid != define.get_ownerid(charid=form.charid):
        raise WeasylError('InsufficientPermissions')

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

    character.reupload(request.userid, form.targetid, form.submitfile)
    raise HTTPSeeOther(location="/character/%i" % (form.targetid,))


@login_required
def reupload_cover_get_(request):
    form = request.web_input(submitid="")
    form.submitid = define.get_int(form.submitid)

    if request.userid != define.get_ownerid(submitid=form.submitid):
        raise WeasylError('InsufficientPermissions')

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

    detail = submission.select_view(
        request.userid,
        form.submitid,
        rating=ratings.EXPLICIT.code,
        ignore=False,
        anyway=form.anyway == "true",
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
    form = request.web_input(submitid="", title="", folderid="", subtype="", rating="",
                             content="", embedlink="")

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
                    friends_only='friends' in request.POST, critique='critique' in request.POST)
    raise HTTPSeeOther(location="/submission/%i/%s%s" % (
        define.get_int(form.submitid),
        slug_for(form.title),
        "?anyway=true" if request.userid in staff.MODS else ''
    ))


@login_required
def edit_character_get_(request):
    form = request.web_input(charid="", anyway="")
    form.charid = define.get_int(form.charid)

    detail = character.select_view(
        request.userid,
        form.charid,
        rating=ratings.EXPLICIT.code,
        ignore=False,
        anyway=form.anyway == "true",
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
    form = request.web_input(charid="", title="", age="", gender="", height="",
                             weight="", species="", rating="", content="")

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

    character.edit(request.userid, c, friends_only='friends' in request.POST)
    raise HTTPSeeOther(location="/character/%i/%s%s" % (
        define.get_int(form.charid),
        slug_for(form.title),
        ("?anyway=true" if request.userid in staff.MODS else '')
    ))


@login_required
def edit_journal_get_(request):
    form = request.web_input(journalid="", anyway="")
    form.journalid = define.get_int(form.journalid)

    detail = journal.select_view(
        request.userid,
        form.journalid,
        rating=ratings.EXPLICIT.code,
        ignore=False,
        anyway=form.anyway == "true",
    )

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
    form = request.web_input(journalid="", title="", rating="", content="")

    rating = ratings.CODE_MAP.get(define.get_int(form.rating))
    if not rating:
        raise WeasylError("ratingInvalid")

    j = orm.Journal()
    j.journalid = define.get_int(form.journalid)
    j.title = form.title
    j.rating = rating
    j.content = form.content
    journal.edit(request.userid, j, friends_only='friends' in request.POST)
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


@token_checked
def views_post(request):
    feature = request.matchdict["content_type"]
    targetid = expect_id(request.matchdict["content_id"])

    page_views = define.common_view_content(request.userid, targetid, feature)

    if feature == "users" and not define.shows_statistics(viewer=request.userid, target=targetid):
        page_views = None

    return HTTPNoContent() if page_views is None else Response(
        str(page_views),
        content_type="text/plain;charset=us-ascii",
    )

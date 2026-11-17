from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define, collection, profile
from weasyl.error import WeasylError
from weasyl.controllers.decorators import login_required, token_checked


@login_required
def collection_options_get_(request):
    jsonb_settings = define.get_profile_settings(request.userid)
    form_settings = {
        "allow_request": jsonb_settings.allow_collection_requests,
        "allow_notification": jsonb_settings.allow_collection_notifs,
    }
    return Response(define.webpage(request.userid, "manage/collection_options.html", [form_settings], title="Collection Options"))


@login_required
@token_checked
def collection_options_post_(request):
    profile.set_collection_preferences(
        request.userid,
        allow_requests="allow_request" in request.POST,
        notify="allow_notification" in request.POST,
    )

    raise HTTPSeeOther(location="/control")


@login_required
@token_checked
def collection_offer_(request):
    recipient_name = request.POST.get("recipient")
    # TODO: remove this fallback name for the recipient field after the replacement has been deployed for a while
    if recipient_name is None:
        recipient_name = request.POST.getone("username")

    form = request.web_input(submitid="")
    form.otherid = profile.resolve(None, None, recipient_name)
    form.submitid = int(form.submitid)

    if not form.otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == form.otherid:
        raise WeasylError("cannotSelfCollect")

    collection.offer(request.userid, form.submitid, form.otherid)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your collection offer has been sent "
        "and the recipient may now add this submission to their gallery.",
    ))


@login_required
@token_checked
def collection_request_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(submitid="")
    form.submitid = int(form.submitid)
    form.otherid = define.get_ownerid(submitid=form.submitid)

    if not form.otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == form.otherid:
        raise WeasylError("cannotSelfCollect")

    collection.request(request.userid, form.submitid, form.otherid)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your collection request has been sent. "
        "The submission author may approve or reject this request.",
    ))


@login_required
@token_checked
def collection_remove_(request):
    form = request.web_input(submissions=[])
    # submissions input format: "submissionID;collectorID"
    submissions = [int(x.split(";")[0]) for x in form.submissions]

    collection.remove(request.userid, submissions)
    raise HTTPSeeOther(location="/manage/collections")

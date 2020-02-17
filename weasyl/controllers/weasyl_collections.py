from __future__ import absolute_import

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
    jsonb_settings = define.get_profile_settings(request.userid)
    jsonb_settings.allow_collection_requests = 'allow_request' in request.params
    jsonb_settings.allow_collection_notifs = 'allow_notification' in request.params

    profile.edit_preferences(request.userid, jsonb_settings=jsonb_settings)
    raise HTTPSeeOther(location="/control")


@login_required
@token_checked
def collection_offer_(request):
    otherid = profile.resolve(None, None, request.params.get('username'))
    submitid = int(request.params.get('submitid'))

    if not otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == otherid:
        raise WeasylError("cannotSelfCollect")

    collection.offer(request.userid, submitid, otherid)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your collection offer has been sent "
        "and the recipient may now add this submission to their gallery.",
        [["Go Back", "/submission/%i" % (submitid,)], ["Return to the Home Page", "/index"]]))


@login_required
@token_checked
def collection_request_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    submitid = int(request.params.get('submitid'))
    otherid = define.get_ownerid(submitid=submitid)

    if not otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == otherid:
        raise WeasylError("cannotSelfCollect")

    collection.request(request.userid, submitid, otherid)
    return Response(define.errorpage(
        request.userid,
        "**Success!** Your collection request has been sent. "
        "The submission author may approve or reject this request.",
        [["Go Back", "/submission/%i" % (submitid,)], ["Return to the Home Page", "/index"]]))


@login_required
@token_checked
def collection_remove_(request):
    # submissions input format: "submissionID;collectorID"
    submissions = [int(x.split(";")[0]) for x in request.getall('submissions')]

    collection.remove(request.userid, submissions)
    raise HTTPSeeOther(location="/manage/collections")

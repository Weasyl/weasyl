import arrow

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define, macro, moderation, note, profile, report
from weasyl.controllers.decorators import moderator_only, token_checked
from weasyl.error import WeasylError
from weasyl.forms import expect_id
from weasyl.forms import expect_ids


# Moderator control panel functions
@moderator_only
def modcontrol_(request):
    return Response(define.webpage(request.userid, "modcontrol/modcontrol.html", title="Moderator Control Panel"))


@moderator_only
def modcontrol_suspenduser_get_(request):
    return Response(define.webpage(request.userid, "modcontrol/suspenduser.html",
                                   (),
                                   options=("mod",),
                                   title="User Suspensions"))


@moderator_only
@token_checked
def modcontrol_suspenduser_post_(request):
    form = request.web_input(userid="", username="", mode="", reason="", datetype="",
                             duration="", durationunit="")

    moderation.setusermode(request.userid, form)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
def modcontrol_report_(request):
    r = report.select_view(request.userid, reportid=int(request.GET["reportid"]))
    blacklisted_tags = moderation.gallery_blacklisted_tags(request.userid, r.target.userid)

    return Response(define.webpage(request.userid, "modcontrol/report.html", [
        request.userid,
        r,
        blacklisted_tags,
    ], options=("mod",), title="View Reported " + r.target_type.title()))


@moderator_only
def modcontrol_reports_(request):
    form = request.web_input(status="open", violation="", submitter="")
    return Response(define.webpage(request.userid, "modcontrol/reports.html", [
        # Method
        {"status": form.status, "violation": int(form.violation or -1), "submitter": form.submitter},
        # Reports
        report.select_list(request.userid, form),
        macro.MACRO_REPORT_VIOLATION,
    ], options=("mod",), title="Reported Content"))


@moderator_only
@token_checked
def modcontrol_closereport_(request):
    form = request.web_input(reportid='', action='')
    report.close(request.userid, form)
    raise HTTPSeeOther(location="/modcontrol/report?reportid=%d" % (int(form.reportid),))


@moderator_only
def modcontrol_contentbyuser_(request):
    form = request.web_input(name='', features=[])

    # Does the target user exist? There's no sense in displaying a blank page if not.
    target_userid = profile.resolve(None, None, form.name)
    if not target_userid:
        raise WeasylError("userRecordMissing")

    submissions = moderation.submissionsbyuser(target_userid) if 's' in form.features else []
    characters = moderation.charactersbyuser(target_userid) if 'c' in form.features else []
    journals = moderation.journalsbyuser(target_userid) if 'j' in form.features else []

    return Response(define.webpage(request.userid, "modcontrol/contentbyuser.html", [
        form.name,
        sorted(submissions + characters + journals, key=lambda item: item['unixtime'], reverse=True),
    ], options=("mod",), title=form.name + "'s Content"))


@moderator_only
@token_checked
def modcontrol_massaction_(request):
    action = request.POST.getone("action")

    if action.startswith("zap-"):
        # "Zapping" cover art or thumbnails is not a bulk edit.
        submitid = expect_id(request.POST.getone("submissions"))

        match action:
            case "zap-cover":
                moderation.removecoverart(request.userid, submitid)
            case "zap-thumb":
                moderation.removethumbnail(request.userid, submitid)
            case "zap-both":
                moderation.removecoverart(request.userid, submitid)
                moderation.removethumbnail(request.userid, submitid)
            case _:  # pragma: no cover
                raise WeasylError("Unexpected")
        raise HTTPSeeOther(location="/submission/%i" % (submitid,))

    submissions = expect_ids(request.POST.getall("submissions"))
    characters = expect_ids(request.POST.getall("characters"))
    journals = expect_ids(request.POST.getall("journals"))

    return Response(
        content_type='text/plain',
        body=moderation.bulk_edit(
            request.userid,
            action=action,
            submissions=submissions,
            characters=characters,
            journals=journals,
        ),
    )


@moderator_only
def modcontrol_manageuser_(request):
    form = request.web_input(name="")

    return Response(define.webpage(request.userid, "modcontrol/manageuser.html", [
        moderation.manageuser(request.userid, form),
    ], title="User Management"))


@moderator_only
@token_checked
def modcontrol_removeavatar_(request):
    form = request.web_input(userid="")

    moderation.removeavatar(request.userid, define.get_int(form.userid))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_removebanner_(request):
    form = request.web_input(userid="")

    moderation.removebanner(request.userid, define.get_int(form.userid))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editprofiletext_(request):
    form = request.web_input(userid="", content="")

    moderation.editprofiletext(request.userid, define.get_int(form.userid), form.content)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editcatchphrase_(request):
    form = request.web_input(userid="", content="")

    moderation.editcatchphrase(request.userid, define.get_int(form.userid), form.content)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_copynotetostaffnotes_post_(request):
    form = request.web_input(noteid=None)

    notedata = note.select_view(request.userid, int(form.noteid))

    staff_note_title = "Received note from {sender}, dated {date}, with subject: “{subj}”.".format(
        sender=notedata['sendername'],
        date=arrow.get(notedata['unixtime']).format('YYYY-MM-DD HH:mm:ss ZZ'),
        subj=notedata['title'],
    )

    moderation.note_about(
        userid=request.userid,
        target_user=notedata['senderid'],
        title=staff_note_title,
        message=notedata['content'],
    )
    raise HTTPSeeOther("/staffnotes/" + notedata['sendername'])

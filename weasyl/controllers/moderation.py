# encoding: utf-8

from __future__ import absolute_import

import anyjson as json
import arrow

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl.controllers.decorators import moderator_only, token_checked
from weasyl.error import WeasylError
from weasyl import define, macro, moderation, note, report


# Moderator control panel functions
@moderator_only
def modcontrol_(request):
    return Response(define.webpage(request.userid, "modcontrol/modcontrol.html"))


@moderator_only
def modcontrol_suspenduser_get_(request):
    return Response(define.webpage(request.userid, "modcontrol/suspenduser.html",
                                   [moderation.BAN_TEMPLATES, json.dumps(moderation.BAN_TEMPLATES)]))


@moderator_only
@token_checked
def modcontrol_suspenduser_post_(request):
    form = request.web_input(userid="", username="", mode="", reason="", day="", month="", year="", datetype="",
                             duration="", durationunit="")

    moderation.setusermode(request.userid, form)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
def modcontrol_report_(request):
    form = request.web_input(reportid='')
    r = report.select_view(request.userid, form)
    blacklisted_tags = moderation.gallery_blacklisted_tags(request.userid, r.target.userid)

    return Response(define.webpage(request.userid, "modcontrol/report.html", [
        request.userid,
        r,
        blacklisted_tags,
    ]))


@moderator_only
def modcontrol_reports_(request):
    form = request.web_input(status="open", violation="", submitter="")
    return Response(define.webpage(request.userid, "modcontrol/reports.html", [
        # Method
        {"status": form.status, "violation": int(form.violation or -1), "submitter": form.submitter},
        # Reports
        report.select_list(request.userid, form),
        macro.MACRO_REPORT_VIOLATION,
    ]))


@moderator_only
@token_checked
def modcontrol_closereport_(request):
    form = request.web_input(reportid='', action='')
    report.close(request.userid, form)
    raise HTTPSeeOther(location="/modcontrol/report?reportid=%d" % (int(form.reportid),))


@moderator_only
def modcontrol_contentbyuser_(request):
    form = request.web_input(name='', features=[])

    submissions = moderation.submissionsbyuser(request.userid, form) if 's' in form.features else []
    characters = moderation.charactersbyuser(request.userid, form) if 'c' in form.features else []
    journals = moderation.journalsbyuser(request.userid, form) if 'j' in form.features else []

    return Response(define.webpage(request.userid, "modcontrol/contentbyuser.html", [
        form.name,
        sorted(submissions + characters + journals, key=lambda item: item['unixtime'], reverse=True),
    ]))


@moderator_only
@token_checked
def modcontrol_massaction_(request):
    form = request.web_input(action='', name='', submissions=[], characters=[], journals=[])
    if form.action.startswith("zap-"):
        # "Zapping" cover art or thumbnails is not a bulk edit.
        if not form.submissions:
            raise WeasylError("Unexpected")
        submitid = int(form.submissions[0])
        type = form.action.split("zap-")[1]
        if type == "cover":
            moderation.removecoverart(request.userid, submitid)
        elif type == "thumb":
            moderation.removethumbnail(request.userid, submitid)
        elif type == "both":
            moderation.removecoverart(request.userid, submitid)
            moderation.removethumbnail(request.userid, submitid)
        else:
            raise WeasylError("Unexpected")
        raise HTTPSeeOther(location="/submission/%i" % (submitid,))

    return Response(
        content_type='text/plain',
        body=moderation.bulk_edit(
            request.userid,
            form.action,
            map(int, form.submissions),
            map(int, form.characters),
            map(int, form.journals),
        ),
    )


@moderator_only
@token_checked
def modcontrol_hide_(request):
    form = request.web_input(name="", submission="", character="")

    if form.submission:
        moderation.hidesubmission(int(form.submission))
    elif form.character:
        moderation.hidecharacter(int(form.character))

    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_unhide_(request):
    form = request.web_input(name="", submission="", character="")

    if form.submission:
        moderation.unhidesubmission(int(form.submission))
    elif form.character:
        moderation.unhidecharacter(int(form.character))

    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
def modcontrol_manageuser_(request):
    form = request.web_input(name="")

    return Response(define.webpage(request.userid, "modcontrol/manageuser.html", [
        moderation.manageuser(request.userid, form),
    ]))


@moderator_only
@token_checked
def modcontrol_removeavatar_(request):
    form = request.web_input(userid="")

    moderation.removeavatar(request.userid, define.get_int_DEPRECIATED(form.userid))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_removebanner_(request):
    form = request.web_input(userid="")

    moderation.removebanner(request.userid, define.get_int_DEPRECIATED(form.userid))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editprofiletext_(request):
    form = request.web_input(userid="", content="")

    moderation.editprofiletext(request.userid, define.get_int_DEPRECIATED(form.userid), form.content)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editcatchphrase_(request):
    form = request.web_input(userid="", content="")

    moderation.editcatchphrase(request.userid, define.get_int_DEPRECIATED(form.userid), form.content)
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_edituserconfig_(request):
    form = request.web_input(userid="")

    moderation.edituserconfig(form)
    raise HTTPSeeOther("/modcontrol")


@moderator_only
@token_checked
def modcontrol_copynotetostaffnotes_post_(request):
    form = request.web_input(noteid=None)

    notedata = note.select_view(request.userid, int(form.noteid))

    staff_note_title = u"Received note from {sender}, dated {date}, with subject: “{subj}”.".format(
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

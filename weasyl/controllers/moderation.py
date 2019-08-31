# encoding: utf-8

from __future__ import absolute_import

import arrow

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl import define, index, macro, moderation, note, profile, report, spam_filtering, welcome
from weasyl.controllers.decorators import moderator_only, token_checked
from weasyl.error import WeasylError


# Moderator control panel functions
@moderator_only
def modcontrol_(request):
    return Response(define.webpage(request.userid, "modcontrol/modcontrol.html", title="Moderator Control Panel"))


@moderator_only
def modcontrol_suspenduser_get_(request):
    return Response(define.webpage(request.userid, "modcontrol/suspenduser.html",
                                   (moderation.BAN_TEMPLATES,), title="User Suspensions"))


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
    ], title="View Reported " + r.target_type.title()))


@moderator_only
def modcontrol_reports_(request):
    form = request.web_input(status="open", violation="", submitter="")
    return Response(define.webpage(request.userid, "modcontrol/reports.html", [
        # Method
        {"status": form.status, "violation": int(form.violation or -1), "submitter": form.submitter},
        # Reports
        report.select_list(request.userid, form),
        macro.MACRO_REPORT_VIOLATION,
    ], title="Reported Content"))


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

    submissions = moderation.submissionsbyuser(request.userid, form) if 's' in form.features else []
    characters = moderation.charactersbyuser(request.userid, form) if 'c' in form.features else []
    journals = moderation.journalsbyuser(request.userid, form) if 'j' in form.features else []

    return Response(define.webpage(request.userid, "modcontrol/contentbyuser.html", [
        form.name,
        sorted(submissions + characters + journals, key=lambda item: item['unixtime'], reverse=True),
    ], title=form.name + "'s Content"))


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


@moderator_only
def modcontrol_spamqueue_journal_get_(request):
    """
    A Pyramid route controller for displaying any journal items which the spam filter has tagged as being spam.
    :param request: The Pyramid request.
    :return: A rendered page for the journal spam queue.
    """
    query = define.engine.execute("""
        SELECT lo.login_name, jo.journalid, jo.title, jo.content
        FROM login lo
        INNER JOIN journal jo USING (userid)
        WHERE jo.is_spam IS TRUE
    """).fetchall()
    return Response(define.webpage(
        request.userid,
        "modcontrol/spamqueue/journal.html",
        [query],
        title="Journal Spam Queue"
    ))


@moderator_only
@token_checked
def modcontrol_spamqueue_journal_post_(request):
    """
    A Pyramid route controller for approving for display or items which the spam filter has tagged as being spam.
    :param request: The Pyramid request.
    :return/raises: HTTPSeeOther for the journal spam queue.
    """
    directive = request.params.get("directive")
    if directive:
        journalid, action = directive.split(",")
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/journal")

    if action == "approve":
        # Approve and insert the journal into the notifications table.
        userid, rating, settings, content, ua_id, ip_addr = define.engine.execute("""
            UPDATE journal
            SET is_spam = FALSE
            WHERE journalid = %(id)s
            RETURNING userid, rating, settings, content, submitter_user_agent_id, submitter_ip_address
        """, id=journalid)
        # Update the spam filtering backend to indicate that this was not spam
        spam_filtering.submit(
            is_ham=True,
            user_ip=ip_addr,
            user_agent_id=ua_id,
            user_id=userid,
            comment_type="journal",
            comment_content=content,
        )
        welcome.journal_insert(userid=userid, journalid=journalid, rating=rating, settings=settings)
    elif action == "delete":
        # Delete and purge the journal from the welcome table
        define.engine.execute("""
            DELETE FROM journal
            WHERE journalid = %(id)s
        """, id=journalid)
        welcome.journal_remove(journalid=journalid)
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/journal")

    raise HTTPSeeOther("/modcontrol/spamqueue/journal")


@moderator_only
def modcontrol_spamqueue_submission_get_(request):
    """
    A Pyramid route controller for displaying any journal items which the spam filter has tagged as being spam.
    :param request: The Pyramid request.
    :return: A rendered page for the journal spam queue.
    """
    query = define.engine.execute("""
        SELECT lo.login_name, su.submitid, su.title, su.content
        FROM login lo
        INNER JOIN submission su USING (userid)
        WHERE su.is_spam IS TRUE
    """).fetchall()
    return Response(define.webpage(
        request.userid,
        "modcontrol/spamqueue/submission.html",
        [query],
        title="Submission Spam Queue"
    ))


@moderator_only
@token_checked
def modcontrol_spamqueue_submission_post_(request):
    """
    A Pyramid route controller for approving for display or items which the spam filter has tagged as being spam.
    :param request: The Pyramid request.
    :return/raises: HTTPSeeOther for the journal spam queue.
    """
    directive = request.params.get("directive")
    if directive:
        submitid, action = directive.split(",")
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/journal")

    if action == "approve":
        # Approve and insert the journal into the notifications table.
        userid, rating, settings, content, ua_id, ip_addr = define.engine.execute("""
            UPDATE submission
            SET is_spam = FALSE
            WHERE submitid = %(id)s
            RETURNING userid, rating, settings, content, submitter_user_agent_id, submitter_ip_address
        """, id=submitid)
        # Update the spam filtering backend to indicate that this was not spam
        spam_filtering.submit(
            is_ham=True,
            user_ip=ip_addr,
            user_agent_id=ua_id,
            user_id=userid,
            comment_type="submission",
            comment_content=content,
        )
        welcome.submission_insert(userid=userid, submitid=submitid, rating=rating, settings=settings)
    elif action == "delete":
        # Delete and purge the journal from the welcome table
        define.engine.execute("""
            DELETE FROM submission
            WHERE submitid = %(id)s
        """, id=submitid)
        welcome.submission_remove(submitid=submitid)
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/journal")

    raise HTTPSeeOther("/modcontrol/spamqueue/journal")


@moderator_only
@token_checked
def modcontrol_deletespam_journal_post_(request):
    """
    Submits a spam journal to the filtering backend, deletes, and removes it from the welcome table.
    :param request: The Pyramid request.
    :return/raises: HTTPSeeOther to /modcontrol/suspenduser
    """
    journalid = request.params.get("journalid")
    if journalid:
        # Delete and get information...
        userid, content, ua_id, ip_addr = define.engine.execute("""
            DELETE FROM journal
            WHERE journalid = %(id)s
            RETURNING userid, content, submitter_user_agent_id, submitter_ip_address
        """, id=journalid).first()
        # Remove from notifications...
        welcome.journal_remove(journalid=journalid)
        # Submit to the backend...
        spam_filtering.submit(
            is_spam=True,
            user_ip=ip_addr,
            user_agent_id=ua_id,
            user_id=userid,
            comment_type="journal",
            comment_content=content,
        )
    index.recent_submissions.invalidate()
    raise HTTPSeeOther("/modcontrol/suspenduser")


@moderator_only
@token_checked
def modcontrol_deletespam_submission_post_(request):
    """
    Submits a spam journal to the filtering backend, deletes, and removes it from the welcome table.
    :param request: The Pyramid request.
    :return/raises: HTTPSeeOther to /modcontrol/suspenduser
    """
    submitid = request.params.get("journalid")
    if submitid:
        # Delete and get information...
        userid, content, ua_id, ip_addr = define.engine.execute("""
            DELETE FROM submission
            WHERE submitid = %(id)s
            RETURNING userid, content, submitter_user_agent_id, submitter_ip_address
        """, id=submitid).first()
        # Remove from notifications...
        welcome.submission_remove(submitid=submitid)
        # Submit to the backend...
        spam_filtering.submit(
            is_spam=True,
            user_ip=ip_addr,
            user_agent_id=ua_id,
            user_id=userid,
            comment_type="submission",
            comment_content=content,
        )
    index.recent_submissions.invalidate()
    raise HTTPSeeOther("/modcontrol/suspenduser")

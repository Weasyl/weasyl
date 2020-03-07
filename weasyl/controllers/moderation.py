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
    moderation.setusermode(
        userid=request.userid,
        targetid=request.params.get('userid', ''),
        username=request.params.get('username', ''),
        mode=request.params.get('mode', ''),
        reason=request.params.get('reason', ''),
        datetype=request.params.get('datetype', ''),
        duration=request.params.get('duration', ''),
        durationunit=request.params.get('durationunit', ''),
        year=request.params.get('year', ''),
        month=request.params.get('month', ''),
        day=request.params.get('day', '')
    )
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
def modcontrol_report_(request):
    r = report.select_view(request.params.get('reportid', ''))
    blacklisted_tags = moderation.gallery_blacklisted_tags(request.userid, r.target.userid)

    return Response(define.webpage(request.userid, "modcontrol/report.html", [
        request.userid,
        r,
        blacklisted_tags,
    ], title="View Reported " + r.target_type.title()))


@moderator_only
def modcontrol_reports_(request):
    form = {
        "status": request.params.get('status', 'open'),
        "violation": request.params.get('violation', '-1'),
        "submitter": request.params.get('submitter', '')
    }
    return Response(define.webpage(request.userid, "modcontrol/reports.html", [
        # Method
        form,
        # Reports
        report.select_list(**form),
        macro.MACRO_REPORT_VIOLATION,
    ], title="Reported Content"))


@moderator_only
@token_checked
def modcontrol_closereport_(request):
    report.close(
        userid=request.userid,
        reportid=request.params.get('reportid', ''),
        action=request.params.get('action', ''),
        explanation=request.params.get('explanation', ''),
        note_title=request.params.get('note_title', ''),
        note_content=request.params.get('user_note', ''),
        assign='assign' in request.params,
        unassign='unassign' in request.params,
        close_all_user_reports='close_all_user_reports' in request.params
    )
    raise HTTPSeeOther(location="/modcontrol/report?reportid=%d" % (int(request.params['reportid']),))


@moderator_only
def modcontrol_contentbyuser_(request):
    name = request.params.get('name', '')
    features = request.params.getall('features')

    # Does the target user exist? There's no sense in displaying a blank page if not.
    target_userid = profile.resolve(None, None, name)
    if not target_userid:
        raise WeasylError("userRecordMissing")

    submissions = moderation.submissionsbyuser(target_userid) if 's' in features else []
    characters = moderation.charactersbyuser(target_userid) if 'c' in features else []
    journals = moderation.journalsbyuser(target_userid) if 'j' in features else []

    return Response(define.webpage(request.userid, "modcontrol/contentbyuser.html", [
        name,
        sorted(submissions + characters + journals, key=lambda item: item['unixtime'], reverse=True),
    ], title=name + "'s Content"))


@moderator_only
@token_checked
def modcontrol_massaction_(request):
    action = request.params.get('action', '')
    submissions = request.params.getall('submissions')
    characters = request.params.getall('characters')
    journals = request.params.getall('journals')
    if action.startswith("zap-"):
        # "Zapping" cover art or thumbnails is not a bulk edit.
        if not submissions:
            raise WeasylError("Unexpected")
        submitid = int(submissions[0])
        type = action.split("zap-")[1]
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
            action,
            map(int, submissions),
            map(int, characters),
            map(int, journals),
        ),
    )


@moderator_only
@token_checked
def modcontrol_hide_(request):
    if request.params.get('submission'):
        moderation.hidesubmission(int(request.params['submission']))
    elif request.params.get('character'):
        moderation.hidecharacter(int(request.params['character']))

    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_unhide_(request):
    if request.params.get('submission'):
        moderation.unhidesubmission(int(request.params.get('submission')))
    elif request.params.get('character'):
        moderation.unhidecharacter(int(request.params.get('character')))

    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
def modcontrol_manageuser_(request):
    return Response(define.webpage(request.userid, "modcontrol/manageuser.html", [
        moderation.manageuser(request.userid, request.params.get('name', '')),
    ], title="User Management"))


@moderator_only
@token_checked
def modcontrol_removeavatar_(request):
    moderation.removeavatar(request.userid, define.get_int(request.params.get('userid', '')))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_removebanner_(request):
    moderation.removebanner(request.userid, define.get_int(request.params.get('userid', '')))
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editprofiletext_(request):
    moderation.editprofiletext(
        request.userid,
        define.get_int(request.params.get('userid', '')),
        request.params.get('content', '')
    )
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_editcatchphrase_(request):
    moderation.editcatchphrase(
        request.userid,
        define.get_int(request.params.get('userid', '')),
        request.params.get('content', '')
    )
    raise HTTPSeeOther(location="/modcontrol")


@moderator_only
@token_checked
def modcontrol_copynotetostaffnotes_post_(request):
    notedata = note.select_view(request.userid, int(request.params['noteid']))

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

    Only displays items that have the `is_spam` flag set, and are not hidden (which is used as the 'reviewed' flag).

    :param request: The Pyramid request.
    :return: A rendered page for the journal spam queue.
    """
    query = define.engine.execute("""
        SELECT lo.login_name, jo.journalid, jo.title, jo.content
        FROM login lo
        INNER JOIN journal jo USING (userid)
        WHERE jo.is_spam
            AND jo.settings !~ 'h'
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
    action = request.params.get("directive")
    journalid = int(request.params.get("journalid"))

    if action == "approve":
        # Approve and insert the journal into the notifications table.
        journalid, userid, rating, settings, content, ua_id, ip_addr = define.engine.execute("""
            UPDATE journal
            SET is_spam = FALSE
            WHERE journalid = %(id)s
            RETURNING journalid, userid, rating, settings, content, submitter_user_agent_id, submitter_ip_address
        """, id=journalid).first()
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
    elif action == "reject":
        moderation.hidejournal(journalid=journalid)
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/journal")

    raise HTTPSeeOther("/modcontrol/spamqueue/journal")


@moderator_only
def modcontrol_spamqueue_submission_get_(request):
    """
    A Pyramid route controller for displaying any journal items which the spam filter has tagged as being spam.

    Only displays items that have the `is_spam` flag set, and are not hidden (which is used as the 'reviewed' flag).

    :param request: The Pyramid request.
    :return: A rendered page for the journal spam queue.
    """
    query = define.engine.execute("""
        SELECT lo.login_name, su.submitid, su.title, su.content
        FROM login lo
        INNER JOIN submission su USING (userid)
        WHERE su.is_spam
            AND su.settings !~ 'h'
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
    action = request.params.get("directive")
    submitid = int(request.params.get("submitid"))

    if action == "approve":
        # Approve and insert the journal into the notifications table.
        submitid, userid, rating, settings, content, ua_id, ip_addr = define.engine.execute("""
            UPDATE submission
            SET is_spam = FALSE
            WHERE submitid = %(id)s
            RETURNING submitid, userid, rating, settings, content, submitter_user_agent_id, submitter_ip_address
        """, id=submitid).first()
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
    elif action == "reject":
        moderation.hidesubmission(submitid=submitid)
    else:
        raise HTTPSeeOther("/modcontrol/spamqueue/submission")

    raise HTTPSeeOther("/modcontrol/spamqueue/submission")


@moderator_only
@token_checked
def modcontrol_spam_remove_post_(request):
    """
    Submits content to the spam filtering backend, and hides it from view.

    Either `submitid` or `journalid` must be present in the request's parameters.

    :param request: The Pyramid request.
    :subparam request.params['submitid']: If present, the submission's ID number.
    :subparam request.params['journalid']: If present, the journal's ID number.
    :return/raises: HTTPSeeOther to /modcontrol/suspenduser.
    """
    submitid = request.params.get('submitid')
    journalid = request.params.get('journalid')

    # Only one parameter should ever be set
    if sum(item is not None for item in [submitid, journalid]) != 1:
        raise WeasylError("Unexpected")

    submitid = int(submitid) if submitid is not None else None
    journalid = int(journalid) if journalid is not None else None

    # Only pkey_value is untrusted input to this statement.
    statement = """
        SELECT userid, content, submitter_user_agent_id, submitter_ip_address
        FROM {table_name}
        WHERE {pkey_name} = %(pkey_value)s
    """

    if submitid:
        # The content_type parameter which will be used to signal to the filtering backend what kind of content this is.
        content_type = "submission"
        statement = statement.format(table_name="submission", pkey_name="submitid")
        record_identifier = submitid
        welcome.submission_remove(submitid=submitid)
        moderation.hidesubmission(submitid=submitid)
    elif journalid:
        content_type = "journal"
        statement = statement.format(table_name="journal", pkey_name="journalid")
        record_identifier = journalid
        welcome.journal_remove(journalid=journalid)
        moderation.hidejournal(journalid=journalid)

    userid, content, user_agent_id, ip_addr = define.engine.execute(statement, pkey_value=record_identifier).first()

    spam_filtering.submit(
        is_spam=True,
        user_ip=ip_addr,
        user_agent_id=user_agent_id,
        user_id=userid,
        comment_type=content_type,
        comment_content=content,
    )

    index.recent_submissions.invalidate()

    raise HTTPSeeOther("/modcontrol/suspenduser")

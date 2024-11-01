from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl.controllers.decorators import login_required, token_checked
from weasyl.error import WeasylError
from weasyl import (
    define, favorite, followuser, forms, frienduser, ignoreuser, note, pagination, profile)


# User interactivity functions
@login_required
@token_checked
def followuser_(request):
    form = request.web_input(userid="")
    otherid = define.get_int(form.userid)

    if request.userid == otherid:
        raise WeasylError("cannotSelfFollow")

    if form.action == "follow":
        followuser.insert(request.userid, otherid)
    elif form.action == "unfollow":
        followuser.remove(request.userid, otherid)

    raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


@login_required
@token_checked
def unfollowuser_(request):
    form = request.web_input(userid="")
    form.otherid = define.get_int(form.userid)

    followuser.remove(request.userid, form.otherid)

    raise HTTPSeeOther(location="/manage/following")


@login_required
@token_checked
def frienduser_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(userid="")
    otherid = define.get_int(form.userid)

    if request.userid == otherid:
        raise WeasylError('cannotSelfFriend')

    if form.action == "sendfriendrequest":
        if not frienduser.check(request.userid, otherid) and not frienduser.already_pending(request.userid, otherid):
            frienduser.request(request.userid, otherid)
    elif form.action == "withdrawfriendrequest":
        if frienduser.already_pending(request.userid, otherid):
            frienduser.remove_request(request.userid, otherid)
    elif form.action == "unfriend":
        frienduser.remove(request.userid, otherid)

    if form.feature == "pending":
        raise HTTPSeeOther(location="/manage/friends?feature=pending")
    else:  # typical value will be user
        raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


@login_required
@token_checked
def unfrienduser_(request):
    form = request.web_input(userid="", feature="")
    otherid = define.get_int(form.userid)

    if request.userid == otherid:
        raise WeasylError('cannotSelfFriend')

    frienduser.remove(request.userid, otherid)

    raise HTTPSeeOther(location="/manage/friends?feature=%s" % form.feature)


@login_required
@token_checked
def ignoreuser_(request):
    form = request.web_input(userid="")
    otherid = define.get_int(form.userid)

    if form.action == "ignore":
        ignoreuser.insert(request.userid, [otherid])
    elif form.action == "unignore":
        ignoreuser.remove(request.userid, [otherid])

    raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


# Private messaging functions
@login_required
def note_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    try:
        noteid = forms.expect_id(request.GET.getone("noteid"))
    except (KeyError, WeasylError) as e:
        raise WeasylError("noteRecordMissing") from e

    data = note.select_view(request.userid, noteid)

    return Response(define.webpage(request.userid, "note/message_view.html", [
        # Private message
        data,
        profile.select_myself(request.userid),
    ]))


@login_required
def notes_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(folder="inbox", filter="", backid="", nextid="")

    if form.folder == "inbox":
        select_list = note.select_inbox
        select_count = note.select_inbox_count
        title = "Inbox"
    elif form.folder == "outbox":
        select_list = note.select_outbox
        select_count = note.select_outbox_count
        title = "Sent messages"
    else:
        raise WeasylError("unknownMessageFolder")

    backid = int(form.backid) if form.backid else None
    nextid = int(form.nextid) if form.nextid else None
    filter_ = define.get_userids(define.get_sysname_list(form.filter))

    result = pagination.PaginatedResult(
        select_list, select_count, "noteid", f"/notes?folder={form.folder}&%s",
        request.userid, filter=list(set(filter_.values())),
        backid=backid,
        nextid=nextid,
        count_limit=note.COUNT_LIMIT,
    )
    return Response(define.webpage(request.userid, "note/message_list.html", (
        form.folder,
        result,
        [(sysname, userid != 0) for sysname, userid in filter_.items()],
        note.unread_count(request.userid),
    ), title=title))


@login_required
def notes_compose_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(recipient="")

    return Response(define.webpage(request.userid, "note/compose.html", [
        # Recipient
        "; ".join(define.get_sysname_list(form.recipient)),
        profile.select_myself(request.userid),
    ], title="Compose message"))


@login_required
@token_checked
def notes_compose_post_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(recipient="", title="", content="", mod_copy='', staff_note='')

    try:
        note.send(request.userid, form)
    except ValueError:
        raise WeasylError('recipientInvalid')
    else:
        raise HTTPSeeOther(location="/notes")  # todo (send to /note/xxx ?)


@login_required
@token_checked
def notes_remove_(request):
    form = request.web_input(folder="", backid="", nextid="", notes=[])
    backid = int(form.backid) if form.backid else None
    nextid = int(form.nextid) if form.nextid else None

    note.remove_list(request.userid, list(map(int, form.notes)))
    link = "/notes?folder=" + form.folder

    if backid:
        link += "&backid=%i" % backid
    elif nextid:
        link += "&nextid=%i" % nextid

    raise HTTPSeeOther(location=link)


@login_required
@token_checked
def favorite_(request):
    form = request.web_input(submitid="", charid="", journalid="")
    form.charid = define.get_int(form.charid)
    form.submitid = define.get_int(form.submitid)
    form.journalid = define.get_int(form.journalid)

    if form.action == "favorite":
        favorite.insert(request.userid, form.submitid, form.charid, form.journalid)
    elif form.action == "unfavorite":
        favorite.remove(request.userid, form.submitid, form.charid, form.journalid)

    if form.submitid:
        raise HTTPSeeOther(location="/submission/%i" % (form.submitid,))
    elif form.charid:
        raise HTTPSeeOther(location="/character/%i" % (form.charid,))
    else:
        raise HTTPSeeOther(location="/journal/%i" % (form.journalid,))

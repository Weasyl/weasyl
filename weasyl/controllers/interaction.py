from __future__ import absolute_import

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.response import Response

from weasyl.controllers.decorators import login_required, token_checked
from weasyl.error import WeasylError
from weasyl import (
    define, favorite, followuser, frienduser, ignoreuser, note, profile)


# User interactivity functions
@login_required
@token_checked
def followuser_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    action = request.params.get('action')
    otherid = define.get_int(request.params.get('userid', ''))

    if request.userid == otherid:
        raise WeasylError("cannotSelfFollow")

    if action == "follow":
        followuser.insert(request.userid, otherid)
    elif action == "unfollow":
        followuser.remove(request.userid, otherid)

    raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


@login_required
@token_checked
def unfollowuser_(request):
    otherid = define.get_int(request.params.get('userid', ''))

    followuser.remove(request.userid, otherid)

    raise HTTPSeeOther(location="/manage/following")


@login_required
@token_checked
def frienduser_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    action = request.params.get('action')
    otherid = define.get_int(request.params.get('userid', ''))

    if request.userid == otherid:
        raise WeasylError('cannotSelfFriend')

    if action == "sendfriendrequest":
        if not frienduser.check(request.userid, otherid) and not frienduser.already_pending(request.userid, otherid):
            frienduser.request(request.userid, otherid)
    elif action == "withdrawfriendrequest":
        if frienduser.already_pending(request.userid, otherid):
            frienduser.remove_request(request.userid, otherid)
    elif action == "unfriend":
        frienduser.remove(request.userid, otherid)

    if request.params.get('feature') == "pending":
        raise HTTPSeeOther(location="/manage/friends?feature=pending")
    else:  # typical value will be user
        raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


@login_required
@token_checked
def unfrienduser_(request):
    otherid = define.get_int(request.params.get('userid', ''))

    if request.userid == otherid:
        raise WeasylError('cannotSelfFriend')

    frienduser.remove(request.userid, otherid)

    redirect = "/manage/friends"
    
    if request.params.get('feature') == 'pending':
        redirect += "?feature=pending"

    raise HTTPSeeOther(location=redirect)


@login_required
@token_checked
def ignoreuser_(request):
    action = request.params.get('action')
    otherid = define.get_int(request.params.get('userid', ''))

    if action == "ignore":
        ignoreuser.insert(request.userid, [otherid])
    elif action == "unignore":
        ignoreuser.remove(request.userid, [otherid])

    raise HTTPSeeOther(location="/~%s" % (define.get_sysname(define.get_display_name(otherid))))


# Private messaging functions
@login_required
def note_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    data = note.select_view(request.userid, int(request.params['noteid']))

    return Response(define.webpage(request.userid, "note/message_view.html", [
        # Private message
        data,
        profile.select_myself(request.userid),
    ]))


@login_required
def notes_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    folder = request.params.get('folder', 'inbox')
    backid = request.params.get('backid')
    nextid = request.params.get('nextid')
    backid = int(backid) if backid else None
    nextid = int(nextid) if nextid else None
    filter_ = define.get_userid_list(request.params.get('filter', ''))

    if folder == "inbox":
        return Response(define.webpage(request.userid, "note/message_list.html", [
            # Folder
            "inbox",
            # Private messages
            note.select_inbox(request.userid, 50, backid=backid, nextid=nextid, filter=filter_),
        ]))

    if folder == "outbox":
        return Response(define.webpage(request.userid, "note/message_list.html", [
            # Folder
            "outbox",
            # Private messages
            note.select_outbox(request.userid, 50, backid=backid, nextid=nextid, filter=filter_),
        ]))

    raise WeasylError("unknownMessageFolder")


@login_required
def notes_compose_get_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    return Response(define.webpage(request.userid, "note/compose.html", [
        # Recipient
        request.params.get('recipient', '').strip(),
        profile.select_myself(request.userid),
    ]))


@login_required
@token_checked
def notes_compose_post_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    try:
        note.send(
            userid=request.userid,
            recipient=request.params.get('recipient', ''),
            title=request.params.get('title', ''),
            content=request.params.get('content', ''),
            mod_copy=request.params.get('mod_copy'),
            staff_note=request.params.get('staff_note'),
        )
    except ValueError:
        raise WeasylError('recipientInvalid')
    else:
        raise HTTPSeeOther(location="/notes")  # todo (send to /note/xxx ?)


@login_required
@token_checked
def notes_remove_(request):
    backid = request.params.get('backid')
    nextid = request.params.get('nextid')
    backid = int(backid) if backid else None
    nextid = int(nextid) if nextid else None

    note.remove_list(request.userid, map(int, request.params.getall('notes')))
    link = "/notes?folder=" + request.params.get('folder', '')

    if backid:
        link += "&backid=%i" % backid
    elif nextid:
        link += "&nextid=%i" % nextid

    raise HTTPSeeOther(location=link)


@login_required
@token_checked
def favorite_(request):
    charid = define.get_int(request.params.get('charid', ''))
    submitid = define.get_int(request.params.get('submitid', ''))
    journalid = define.get_int(request.params.get('journalid', ''))
    action = request.params.get('action')

    if action == "favorite":
        favorite.insert(request.userid, submitid, charid, journalid)
    elif action == "unfavorite":
        favorite.remove(request.userid, submitid, charid, journalid)

    if submitid:
        raise HTTPSeeOther(location="/submission/%i" % (submitid,))
    elif charid:
        raise HTTPSeeOther(location="/character/%i" % (charid,))
    else:
        raise HTTPSeeOther(location="/journal/%i" % (journalid,))

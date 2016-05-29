import web

from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError
from weasyl import (
    define, favorite, followuser, frienduser, ignoreuser, note, profile)


# User interactivity functions
class followuser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")
        otherid = define.get_int(form.userid)

        if self.user_id == otherid:
            return define.errorpage(self.user_id, "You cannot follow yourself.")

        if form.action == "follow":
            if not followuser.check(self.user_id, otherid):
                followuser.insert(self.user_id, otherid)
        elif form.action == "unfollow":
            followuser.remove(self.user_id, otherid)

        raise web.seeother("/~%s" % (define.get_sysname(define.get_display_name(otherid))))


class unfollowuser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")
        form.otherid = define.get_int(form.userid)

        followuser.remove(self.user_id, form.otherid)

        return define.errorpage(
            self.user_id, "**Success!** You are no longer following this user.",
            [["Go Back", "/manage/following"], ["Return Home", "/"]])


class frienduser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")
        otherid = define.get_int(form.userid)

        if self.user_id == otherid:
            return define.errorpage(self.user_id, "You cannot friend yourself.")

        if form.action == "sendfriendrequest":
            if not frienduser.check(self.user_id, otherid) and not frienduser.already_pending(self.user_id, otherid):
                frienduser.request(self.user_id, otherid)
        elif form.action == "withdrawfriendrequest":
            if frienduser.already_pending(self.user_id, otherid):
                frienduser.remove_request(self.user_id, otherid)
        elif form.action == "unfriend":
            frienduser.remove(self.user_id, otherid)

        if form.feature == "pending":
            raise web.seeother("/manage/friends?feature=pending")
        else:  # typical value will be user
            raise web.seeother("/~%s" % (define.get_sysname(define.get_display_name(otherid))))


class unfrienduser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="", feature="")
        otherid = define.get_int(form.userid)

        if self.user_id == otherid:
            return define.errorpage(self.user_id, "You cannot friend yourself.")

        frienduser.remove(self.user_id, otherid)

        raise web.seeother("/manage/friends?feature=%s" % form.feature)


class ignoreuser_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(userid="")
        otherid = define.get_int(form.userid)

        if form.action == "ignore":
            if not ignoreuser.check(self.user_id, otherid):
                ignoreuser.insert(self.user_id, otherid)
        elif form.action == "unignore":
            ignoreuser.remove(self.user_id, otherid)

        raise web.seeother("/~%s" % (define.get_sysname(define.get_display_name(otherid))))


# Private messaging functions
class note_(controller_base):
    login_required = True

    def GET(self):
        form = web.input()

        data = note.select_view(self.user_id, int(form.noteid))

        return define.webpage(self.user_id, "note/message_view.html", [
            # Private message
            data,
            profile.select_myself(self.user_id),
        ])


class notes_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(folder="inbox", filter="", backid="", nextid="")
        backid = int(form.backid) if form.backid else None
        nextid = int(form.nextid) if form.nextid else None
        filter_ = define.get_userid_list(form.filter)

        if form.folder == "inbox":
            return define.webpage(self.user_id, "note/message_list.html", [
                # Folder
                "inbox",
                # Private messages
                note.select_inbox(self.user_id, 50, backid=backid, nextid=nextid, filter=filter_),
            ])

        if form.folder == "outbox":
            return define.webpage(self.user_id, "note/message_list.html", [
                # Folder
                "outbox",
                # Private messages
                note.select_outbox(self.user_id, 50, backid=backid, nextid=nextid, filter=filter_),
            ])

        raise WeasylError("unknownMessageFolder")


class notes_compose_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(recipient="")

        return define.webpage(self.user_id, "note/compose.html", [
            # Recipient
            form.recipient.strip(),
            profile.select_myself(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(recipient="", title="", content="", mod_copy='', staff_note='')

        try:
            note.send(self.user_id, form)
        except ValueError:
            raise WeasylError('recipientInvalid')
        else:
            raise web.seeother("/notes")  # todo (send to /note/xxx ?)


class notes_remove_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(folder="", backid="", nextid="", notes=[])
        backid = int(form.backid) if form.backid else None
        nextid = int(form.nextid) if form.nextid else None

        note.remove_list(self.user_id, map(int, form.notes))
        link = "/notes?folder=" + form.folder

        if backid:
            link += "&backid=%i" % backid
        elif nextid:
            link += "&nextid=%i" % nextid

        raise web.seeother(link)


class favorite_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", charid="", journalid="")
        form.charid = define.get_int(form.charid)
        form.submitid = define.get_int(form.submitid)
        form.journalid = define.get_int(form.journalid)

        if form.action == "favorite":
            try:
                favorite.insert(self.user_id, form.submitid, form.charid, form.journalid)
            except WeasylError as we:
                if we.value != "favoriteRecordExists":
                    raise
        elif form.action == "unfavorite":
            favorite.remove(self.user_id, form.submitid, form.charid, form.journalid)

        if form.submitid:
            raise web.seeother("/submission/%i" % (form.submitid,))
        elif form.charid:
            raise web.seeother("/character/%i" % (form.charid,))
        else:
            raise web.seeother("/journal/%i" % (form.journalid,))

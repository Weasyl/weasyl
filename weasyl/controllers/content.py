import urlparse

import web

from libweasyl import ratings
from libweasyl import staff
from libweasyl.models.media import SubmissionMediaLink
from libweasyl.text import slug_for

from weasyl import (
    character, comment, define, errorcode, folder, journal, macro, profile,
    report, searchtag, shout, submission, orm)
from weasyl.controllers.base import controller_base
from weasyl.error import WeasylError


# Content submission functions
class submit_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "submit/submit.html")


class submit_visual_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(title='', tags=[], description='', imageURL='', baseURL='')
        if form.baseURL:
            form.imageURL = urlparse.urljoin(form.baseURL, form.imageURL)

        return define.webpage(self.user_id, "submit/visual.html", [
            # Folders
            folder.select_list(self.user_id, "drop/all"),
            # Subtypes
            [i for i in macro.MACRO_SUBCAT_LIST if 1000 <= i[0] < 2000],
            profile.get_user_ratings(self.user_id),
            form,
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submitfile="", thumbfile="", title="", folderid="",
                         subtype="", rating="", friends="", critique="", content="",
                         tags="", imageURL="")

        tags = searchtag.parse_tags(form.tags)

        if not define.config_read_bool("allow_submit"):
            raise WeasylError("FeatureDisabled")

        rating = ratings.CODE_MAP.get(define.get_int(form.rating))
        if not rating:
            raise WeasylError("ratingInvalid")

        s = orm.Submission()
        s.title = form.title
        s.rating = rating
        s.content = form.content
        s.folderid = define.get_int(form.folderid) or None
        s.subtype = define.get_int(form.subtype)

        submitid = submission.create_visual(
            self.user_id, s, friends_only=form.friends, tags=tags,
            imageURL=form.imageURL, thumbfile=form.thumbfile, submitfile=form.submitfile,
            critique=form.critique, create_notifications=('nonotification' not in form))

        if 'customthumb' in form:
            raise web.seeother("/manage/thumbnail?submitid=%i" % (submitid,))
        else:
            raise web.seeother("/submission/%i/%s" % (submitid, slug_for(form.title)))


class submit_literary_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "submit/literary.html", [
            # Folders
            folder.select_list(self.user_id, "drop/all"),
            # Subtypes
            [i for i in macro.MACRO_SUBCAT_LIST if 2000 <= i[0] < 3000],
            profile.get_user_ratings(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submitfile="", coverfile="boop", thumbfile="", title="",
                         folderid="", subtype="", rating="", friends="", critique="",
                         content="", tags="", embedlink="")

        tags = searchtag.parse_tags(form.tags)

        if not define.config_read_bool("allow_submit"):
            raise WeasylError("FeatureDisabled")

        rating = ratings.CODE_MAP.get(define.get_int(form.rating))
        if not rating:
            raise WeasylError("ratingInvalid")

        s = orm.Submission()
        s.title = form.title
        s.rating = rating
        s.content = form.content
        s.folderid = define.get_int(form.folderid) or None
        s.subtype = define.get_int(form.subtype)

        submitid, thumb = submission.create_literary(
            self.user_id, s, embedlink=form.embedlink, friends_only=form.friends, tags=tags,
            coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
            critique=form.critique, create_notifications=('nonotification' not in form))
        if thumb:
            raise web.seeother("/manage/thumbnail?submitid=%i" % (submitid,))
        else:
            raise web.seeother("/submission/%i/%s" % (submitid, slug_for(form.title)))


class submit_multimedia_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "submit/multimedia.html", [
            # Folders
            folder.select_list(self.user_id, "drop/all"),
            # Subtypes
            [i for i in macro.MACRO_SUBCAT_LIST if 3000 <= i[0] < 4000],
            profile.get_user_ratings(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submitfile="", coverfile="", thumbfile="", embedlink="",
                         title="", folderid="", subtype="", rating="", friends="",
                         critique="", content="", tags="")

        tags = searchtag.parse_tags(form.tags)

        if not define.config_read_bool("allow_submit"):
            raise WeasylError("FeatureDisabled")

        rating = ratings.CODE_MAP.get(define.get_int(form.rating))
        if not rating:
            raise WeasylError("ratingInvalid")

        s = orm.Submission()
        s.title = form.title
        s.rating = rating
        s.content = form.content
        s.folderid = define.get_int(form.folderid) or None
        s.subtype = define.get_int(form.subtype)

        autothumb = ('noautothumb' not in form)

        submitid, thumb = submission.create_multimedia(
            self.user_id, s, embedlink=form.embedlink, friends_only=form.friends, tags=tags,
            coverfile=form.coverfile, thumbfile=form.thumbfile, submitfile=form.submitfile,
            critique=form.critique, create_notifications=('nonotification' not in form),
            auto_thumb=autothumb)
        if thumb and not autothumb:
            raise web.seeother("/manage/thumbnail?submitid=%i" % (submitid,))
        else:
            raise web.seeother("/submission/%i/%s" % (submitid, slug_for(form.title)))


class submit_character_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "submit/character.html", [
            profile.get_user_ratings(self.user_id),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submitfile="", thumbfile="", title="", age="", gender="",
                         height="", weight="", species="", rating="", friends="",
                         content="", tags="")

        tags = searchtag.parse_tags(form.tags)

        if not define.config_read_bool("allow_submit"):
            raise WeasylError("FeatureDisabled")

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

        charid = character.create(self.user_id, c, form.friends, tags,
                                  form.thumbfile, form.submitfile)
        raise web.seeother("/manage/thumbnail?charid=%i" % (charid,))


class submit_journal_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "submit/journal.html", [profile.get_user_ratings(self.user_id)])

    @define.token_checked
    def POST(self):
        form = web.input(title="", rating="", friends="", members="", content="", tags="")

        tags = searchtag.parse_tags(form.tags)

        if not define.config_read_bool("allow_submit"):
            raise WeasylError("FeatureDisabled")

        rating = ratings.CODE_MAP.get(define.get_int(form.rating))
        if not rating:
            raise WeasylError("ratingInvalid")

        j = orm.Journal()
        j.title = form.title
        j.rating = rating
        j.content = form.content
        journalid = journal.create(self.user_id, j, friends_only=form.friends,
                                   tags=tags)
        raise web.seeother("/journal/%i/%s" % (journalid, slug_for(form.title)))


class submit_shout_(controller_base):
    login_required = True

    @define.token_checked
    @define.supports_json
    def POST(self):
        form = web.input(userid="", parentid="", content="", staffnotes="", format="")

        if form.staffnotes and self.user_id not in staff.MODS:
            raise WeasylError("InsufficientPermissions")

        c = orm.Comment()
        c.parentid = define.get_int(form.parentid)
        c.userid = define.get_int(form.userid or form.staffnotes)
        c.content = form.content

        commentid = shout.insert(self.user_id, c, staffnotes=form.staffnotes)

        if form.format == "json":
            return {"id": commentid}

        if form.staffnotes:
            raise web.seeother('/staffnotes?userid=%i#cid%i' % (define.get_int(form.staffnotes), commentid))
        else:
            raise web.seeother("/shouts?userid=%i#cid%i" % (define.get_int(form.userid), commentid))


class submit_comment_(controller_base):
    login_required = True

    @define.token_checked
    @define.supports_json
    def POST(self):
        form = web.input(submitid="", charid="", journalid="", parentid="", content="", format="")

        commentid = comment.insert(self.user_id, charid=define.get_int(form.charid),
                                   parentid=define.get_int(form.parentid),
                                   submitid=define.get_int(form.submitid),
                                   journalid=define.get_int(form.journalid),
                                   content=form.content)

        if form.format == "json":
            return {"id": commentid}

        if define.get_int(form.submitid):
            raise web.seeother("/submission/%i#cid%i" % (define.get_int(form.submitid), commentid))
        elif define.get_int(form.charid):
            raise web.seeother("/character/%i#cid%i" % (define.get_int(form.charid), commentid))
        else:
            raise web.seeother("/journal/%i#cid%i" % (define.get_int(form.journalid), commentid))


class submit_report_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", charid="", journalid="", reportid="", violation="", content="")

        report.create(self.user_id, form)
        if form.reportid:
            raise web.seeother("/modcontrol/report?reportid=%s" % (form.reportid,))
        elif define.get_int(form.submitid):
            raise web.seeother("/submission/%i" % (define.get_int(form.submitid),))
        elif define.get_int(form.charid):
            raise web.seeother("/character/%i" % (define.get_int(form.charid),))
        else:
            raise web.seeother("/journal/%i" % (define.get_int(form.journalid),))


class submit_tags_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", charid="", journalid="", tags="")

        tags = searchtag.parse_tags(form.tags)

        submitid = define.get_int(form.submitid)
        charid = define.get_int(form.charid)
        journalid = define.get_int(form.journalid)

        searchtag.associate(self.user_id, tags, submitid, charid, journalid)
        if submitid:
            raise web.seeother("/submission/%i" % (submitid,))
        elif charid:
            raise web.seeother("/character/%i" % (charid,))
        else:
            raise web.seeother("/journal/%i" % (journalid,))


class reupload_submission_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(submitid="")
        form.submitid = define.get_int(form.submitid)

        if self.user_id != define.get_ownerid(submitid=form.submitid):
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "submit/reupload_submission.html", [
            "submission",
            # SubmitID
            form.submitid,
        ])

    @define.token_checked
    def POST(self):
        form = web.input(targetid="", submitfile="")
        form.targetid = define.get_int(form.targetid)

        if self.user_id != define.get_ownerid(submitid=form.targetid):
            return define.errorpage(self.user_id, errorcode.permission)

        submission.reupload(self.user_id, form.targetid, form.submitfile)
        raise web.seeother("/submission/%i" % (form.targetid,))


class reupload_character_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(charid="")
        form.charid = define.get_int(form.charid)

        if self.user_id != define.get_ownerid(charid=form.charid):
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "submit/reupload_submission.html", [
            "character",
            # charid
            form.charid,
        ])

    @define.token_checked
    def POST(self):
        form = web.input(targetid="", submitfile="")
        form.targetid = define.get_int(form.targetid)

        if self.user_id != define.get_ownerid(charid=form.targetid):
            return define.errorpage(self.user_id, errorcode.permission)

        character.reupload(self.user_id, form.targetid, form.submitfile)
        raise web.seeother("/character/%i" % (form.targetid,))


class reupload_cover_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(submitid="")
        form.submitid = define.get_int(form.submitid)

        if self.user_id != define.get_ownerid(submitid=form.submitid):
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "submit/reupload_cover.html", [form.submitid])

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", coverfile="")
        form.submitid = define.get_int(form.submitid)

        submission.reupload_cover(self.user_id, form.submitid, form.coverfile)
        raise web.seeother("/submission/%i" % (form.submitid,))


# Content editing functions
class edit_submission_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(submitid="", anyway="")
        form.submitid = define.get_int(form.submitid)

        detail = submission.select_view(self.user_id, form.submitid, ratings.EXPLICIT.code, False, anyway=form.anyway)

        if self.user_id != detail['userid'] and self.user_id not in staff.MODS:
            return define.errorpage(self.user_id, errorcode.permission)

        submission_category = detail['subtype'] // 1000 * 1000

        return define.webpage(self.user_id, "edit/submission.html", [
            # Submission detail
            detail,
            # Folders
            folder.select_list(detail['userid'], "drop/all"),
            # Subtypes
            [i for i in macro.MACRO_SUBCAT_LIST
             if submission_category <= i[0] < submission_category + 1000],
            profile.get_user_ratings(detail['userid']),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(submitid="", title="", folderid="", subtype="", rating="",
                         content="", friends="", critique="", embedlink="")

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

        submission.edit(self.user_id, s, embedlink=form.embedlink,
                        friends_only=form.friends, critique=form.critique)
        raise web.seeother("/submission/%i/%s%s" % (define.get_int(form.submitid),
                                                    slug_for(form.title),
                                                    "?anyway=true" if self.user_id in staff.MODS else ''))


class edit_character_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(charid="", anyway="")
        form.charid = define.get_int(form.charid)

        detail = character.select_view(self.user_id, form.charid, ratings.EXPLICIT.code, False, anyway=form.anyway)

        if self.user_id != detail['userid'] and self.user_id not in staff.MODS:
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "edit/character.html", [
            # Submission detail
            detail,
            profile.get_user_ratings(detail['userid']),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(charid="", title="", age="", gender="", height="",
                         weight="", species="", rating="", content="", friends="")

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

        character.edit(self.user_id, c, friends_only=form.friends)
        raise web.seeother("/character/%i/%s%s" % (define.get_int(form.charid),
                                                   slug_for(form.title),
                                                   ("?anyway=true" if self.user_id in staff.MODS else '')))


class edit_journal_(controller_base):
    login_required = True

    def GET(self):
        form = web.input(journalid="", anyway="")
        form.journalid = define.get_int(form.journalid)

        detail = journal.select_view(self.user_id, ratings.EXPLICIT.code, form.journalid, False, anyway=form.anyway)

        if self.user_id != detail['userid'] and self.user_id not in staff.MODS:
            return define.errorpage(self.user_id, errorcode.permission)

        return define.webpage(self.user_id, "edit/journal.html", [
            # Journal detail
            detail,
            profile.get_user_ratings(detail['userid']),
        ])

    @define.token_checked
    def POST(self):
        form = web.input(journalid="", title="", rating="", friends="", content="")

        rating = ratings.CODE_MAP.get(define.get_int(form.rating))
        if not rating:
            raise WeasylError("ratingInvalid")

        j = orm.Journal()
        j.journalid = define.get_int(form.journalid)
        j.title = form.title
        j.rating = rating
        j.content = form.content
        journal.edit(self.user_id, j, friends_only=form.friends)
        raise web.seeother("/journal/%i/%s%s" % (define.get_int(form.journalid),
                                                 slug_for(form.title),
                                                 ("?anyway=true" if self.user_id in staff.MODS else '')))


# Content removal functions
class remove_submission_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(submitid="")

        ownerid = submission.remove(self.user_id, define.get_int(form.submitid))
        if self.user_id == ownerid:
            raise web.seeother("/control")  # todo
        else:
            raise web.seeother("/submissions?userid=%i" % (ownerid,))


class remove_character_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(charid="")

        ownerid = character.remove(self.user_id, define.get_int(form.charid))
        if self.user_id == ownerid:
            raise web.seeother("/control")  # todo
        else:
            raise web.seeother("/characters?userid=%i" % (ownerid,))


class remove_journal_(controller_base):
    login_required = True

    @define.token_checked
    def POST(self):
        form = web.input(journalid="")

        ownerid = journal.remove(self.user_id, define.get_int(form.journalid))
        if self.user_id == ownerid:
            raise web.seeother("/control")  # todo
        else:
            raise web.seeother("/journals?userid=%i" % (ownerid,))


class remove_comment_(controller_base):
    login_required = True

    @define.token_checked
    @define.supports_json
    def POST(self):
        form = web.input(commentid="", feature="", format="")
        commentid = define.get_int(form.commentid)

        if form.feature == "userid":
            targetid = shout.remove(self.user_id, commentid=commentid)
        else:
            targetid = comment.remove(self.user_id, commentid=commentid, feature=form.feature)

        if form.format == "json":
            return {"success": True}

        if form.feature == "userid":
            raise web.seeother("/shouts?userid=%i" % (targetid,))
        elif form.feature == "submit":
            raise web.seeother("/submission/%i" % (targetid,))
        elif form.feature == "char":
            raise web.seeother("/character/%i" % (targetid,))
        elif form.feature == "journal":
            raise web.seeother("/journal/%i" % (targetid,))


class thumb_select_(controller_base):
    login_required = True

    def GET(self):
        # Doing these two calls is wasteful. There's also a slight race condition.
        submission_count = submission.select_count(self.user_id, ratings.EXPLICIT.code, otherid=self.user_id)
        submissions = submission.select_list(self.user_id, ratings.EXPLICIT.code, submission_count, otherid=self.user_id)

        return define.webpage(self.user_id, "manage/thumbnail_opt_out.html", [
            [s for s in submissions if 'thumbnail-legacy' in s['sub_media']],
        ])

    @define.token_checked
    def POST(self):
        selections = [(int(key[:-6]), value) for key, value in web.input().iteritems() if key.endswith("_thumb")]
        remove = [submitid for submitid, selection in selections]
        add_legacy = [submitid for submitid, selection in selections if selection == "old"]

        define.engine.execute("""
            DELETE FROM submission_media_links l
                USING submission_media_links lj, submission s
                WHERE l.submitid = s.submitid
                    AND l.link_type = 'thumbnail-custom'
                    AND s.userid = %(user)s
                    AND lj.submitid = s.submitid
                    AND lj.link_type = 'thumbnail-legacy'
                    AND (l.mediaid = lj.mediaid AND l.submitid = ANY (%(remove)s) OR l.submitid = ANY (%(add_legacy)s));
            INSERT INTO submission_media_links (mediaid, submitid, link_type, attributes)
                SELECT l.mediaid, l.submitid, 'thumbnail-custom', l.attributes
                    FROM submission_media_links l
                        INNER JOIN submission s USING (submitid)
                    WHERE l.link_type = 'thumbnail-legacy'
                        AND l.submitid = ANY (%(add_legacy)s)
                        AND s.userid = %(user)s;
        """, remove=remove, add_legacy=add_legacy, user=self.user_id)

        for submitid in remove:
            SubmissionMediaLink.refresh_cache(submitid)
        # Send the user back to their own submissions.
        raise web.seeother("/submissions?userid=%i" % (self.user_id))

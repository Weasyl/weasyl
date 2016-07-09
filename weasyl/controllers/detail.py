import time

from pyramid import httpexceptions
from pyramid.response import Response
import web

from libweasyl.models.content import Submission
from libweasyl.text import slug_for
from weasyl import (
    character, define, journal, macro, media, profile, searchtag, submission)
from weasyl.controllers.decorators import controller_base
from weasyl.error import WeasylError


# Content detail functions
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')
    now = time.time()

    form = request.web_input(submitid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(form.submitid)

    extras = {
        "pdf": True,
    }

    if define.user_is_twitterbot():
        extras['twitter_card'] = submission.twitter_card(submitid)

    try:
        item = submission.select_view(
            request.userid, submitid, rating,
            ignore=define.text_bool(form.ignore, True), anyway=form.anyway
        )
    except WeasylError as we:
        we.errorpage_kwargs = extras
        if 'twitter_card' in extras:
            extras['options'] = ['nocache']
        if we.value in ("UserIgnored", "TagBlocked"):
            extras['links'] = [
                ("View Submission", "?ignore=false"),
                ("Return to the Home Page", "/index"),
            ]
        raise

    login = define.get_sysname(item['username'])
    if username is not None and login != username:
        raise httpexceptions.HTTPSeeOther(location='/~%s/post/%s/%s' % (login, submitid, slug_for(item["title"])),
                                          headers=request.response.headers)
    extras["canonical_url"] = "/submission/%d/%s" % (submitid, slug_for(item["title"]))
    extras["title"] = item["title"]

    page = define.common_page_start(request.userid, options=["mediaplayer"], **extras)
    page.append(define.render('detail/submission.html', [
        # Myself
        profile.select_myself(request.userid),
        # Submission detail
        item,
        # Subtypes
        macro.MACRO_SUBCAT_LIST,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
    ]))

    return Response(define.common_page_end(request.userid, page, now=now))


def submission_media_(request):
    link_type = request.matchdict['linktype']
    submitid = int(request.matchdict['submitid'])
    if link_type == "submissions":
        link_type = "submission"

    submission = Submission.query.get(submitid)
    if submission is None:
        raise httpexceptions.HTTPForbidden(headers=request.response.headers)
    elif submission.is_hidden or submission.is_friends_only:
        raise httpexceptions.HTTPForbidden(headers=request.response.headers)
    media_items = media.get_submission_media(submitid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound(headers=request.response.headers)
    request.response.headers['X-Accel-Redirect'] = str(media_items[link_type][0]['file_url'])  # Unicode conversion.
    request.response.headers['Cache-Control'] = 'max-age=0'
    return request.response


class submission_tag_history_(controller_base):
    def GET(self, submitid):
        submitid = int(submitid)

        page_title = "Tag updates"
        page = define.common_page_start(self.user_id, title=page_title)
        page.append(define.render('detail/tag_history.html', [
            submission.select_view_api(self.user_id, submitid),
            searchtag.tag_history(submitid),
        ]))
        return define.common_page_end(self.user_id, page)


class character_(controller_base):
    def GET(self, charid=""):
        form = web.input(charid="", ignore="", anyway="")

        rating = define.get_rating(self.user_id)
        charid = define.get_int(charid) if charid else define.get_int(form.charid)

        try:
            item = character.select_view(
                self.user_id, charid, rating,
                ignore=define.text_bool(form.ignore, True), anyway=form.anyway
            )
        except WeasylError as we:
            if we.value in ("UserIgnored", "TagBlocked"):
                we.errorpage_kwargs['links'] = [
                    ("View Character", "?ignore=false"),
                    ("Return to the Home Page", "/index"),
                ]
            raise

        canonical_url = "/character/%d/%s" % (charid, slug_for(item["title"]))

        page = define.common_page_start(self.user_id, canonical_url=canonical_url, title=item["title"])
        page.append(define.render('detail/character.html', [
            # Profile
            profile.select_myself(self.user_id),
            # Character detail
            item,
            # Violations
            [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
        ]))

        return define.common_page_end(self.user_id, page)


class journal_(controller_base):
    def GET(self, journalid=""):
        form = web.input(journalid="", ignore="", anyway="")

        rating = define.get_rating(self.user_id)
        journalid = define.get_int(journalid) if journalid else define.get_int(form.journalid)

        try:
            item = journal.select_view(
                self.user_id, rating, journalid,
                ignore=define.text_bool(form.ignore, True), anyway=form.anyway
            )
        except WeasylError as we:
            if we.value in ("UserIgnored", "TagBlocked"):
                we.errorpage_kwargs['links'] = [
                    ("View Journal", "?ignore=false"),
                    ("Return to the Home Page", "/index"),
                ]
            raise

        canonical_url = "/journal/%d/%s" % (journalid, slug_for(item["title"]))

        page = define.common_page_start(self.user_id, options=["pager"], canonical_url=canonical_url, title=item["title"])
        page.append(define.render('detail/journal.html', [
            # Myself
            profile.select_myself(self.user_id),
            # Journal detail
            item,
            # Violations
            [i for i in macro.MACRO_REPORT_VIOLATION if 3000 <= i[0] < 4000],
        ]))

        return define.common_page_end(self.user_id, page)

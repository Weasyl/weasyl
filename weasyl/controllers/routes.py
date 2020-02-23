from __future__ import absolute_import

from collections import namedtuple
import json
import os.path

from weasyl.controllers import (
    events,
    interaction,
    messages,
    moderation,
    user,
    weasyl_collections,
)
from weasyl import oauth2
from weasyl import macro


Route = namedtuple('Route', ['pattern', 'name', 'view'])

"""
A route to be added to the Weasyl application.

`view` may be either a view callable (in which case only GET/HEAD requests are routed to it) or a
dict mapping http methods to view callables.
"""

# routes = (
#     # OAuth2 routes.
#     Route("/api/oauth2/authorize", "oauth2_authorize",
#           {'GET': oauth2.authorize_get_, 'POST': oauth2.authorize_post_}),
#     Route("/api/oauth2/token", "oauth2_token", {'POST': oauth2.token_}),
#
#     # Routes for static event pages, such as holidays.
#     Route("/events/halloweasyl2014", "events_halloweasyl2014", events.halloweasyl2014_),
# )


def setup_routes_and_views(config):
    """
    Reponsible for setting up all routes for the Weasyl application.

    Args:
        config: A pyramid Configuration for the wsgi application.
    """

    # for route in routes:
    #     if isinstance(route.view, dict):
    #         for method in route.view:
    #             config.add_view(view=route.view[method], route_name=route.name, request_method=method)
    #     else:
    #         config.add_view(view=route.view, route_name=route.name, request_method="GET")

    with open(os.path.join(macro.MACRO_APP_ROOT, 'build/rev-manifest.json'), 'r') as f:
        resource_paths = json.loads(f.read())
        for key, item in resource_paths.items():
            config.add_route(key, item, static=True)


    # Front page views.
    config.add_route("index", "/{index:(index)?}")
    config.add_route("search", "/search")
    config.add_route("popular", "/popular")
    config.add_route("streaming", "/streaming")
    config.add_route("marketplace", "/marketplace")

    # Signin and out views.
    config.add_route("signin", "/signin")
    config.add_route("signout", "/signout")
    config.add_route("signin_2fa_auth", "/signin/2fa-auth")
    config.add_route("signin-unicode-failure", "/signin/unicode-failure")
    config.add_route("signup", "/signup")

    # Verification and password management views.
    config.add_route("forgot_password", "/forgotpassword")
    config.add_route("reset_password", "/resetpassword")
    config.add_route("verify_account", "/verify/account")
    config.add_route("force_reset_password", "/force/resetpassword")
    config.add_route("force_reset_birthday", "/force/resetbirthday")
    config.add_route("verify_emailchange", "/verify/emailchange")
    config.add_route("vouch", "/vouch")

    # Details of specific content
    config.add_route("submission_detail_view_unnamed", "/view")
    config.add_route("submission_detail_view", "/view/{submitid:[0-9]+}{ignore_name:(/.*)?}")
    config.add_route("submission_detail_unnamed", "/submission")
    config.add_route("submission_detail", "/submission/{submitid:[0-9]+}{ignore_name:(/.*)?}")
    config.add_route("submission_detail_profile;no_s;no_slug", "/~{name}/submission/{submitid:[0-9]+}")
    config.add_route("submission_detail_profile;no_s", "/~{name}/submission/{submitid:[0-9]+}/{slug:[^/.]*}")
    config.add_route("submission_detail_profile;no_slug", "/~{name}/submissions/{submitid:[0-9]+}")
    config.add_route("submission_detail_profile", "/~{name}/submissions/{submitid}/{slug}")
    config.add_route("submission_tag_history", "/submission/tag-history/{submitid:[0-9]+}")
    config.add_route("submission_detail_media", "/~{name}/{linktype}/{submitid:[0-9]+}/{ignore_name:.*}")
    config.add_route("character_detail_unnamed", "/character")
    config.add_route("character_detail", "/character/{charid:[0-9]+}/{slug:[^/.]*}")
    config.add_route("journal_detail_unnamedited", "/journal")
    config.add_route("journal_detail", "/journal/{journalid:[0-9]+}/{slug:[^/.]*}")

    # Profile views.
    config.add_route("profile_tilde_unnamed", "/~")
    config.add_route("profile_tilde", "/~{name}")
    config.add_route("profile_user_unnamed", "/user")
    config.add_route("profile_user", "/user/{name}")
    config.add_route("profile_unnamed", "/profile")
    config.add_route("profile", "/profile/{name}")
    config.add_route("profile_submissions_unnamed", "/submissions")
    config.add_route("profile_submissions", "/submissions/{name:[^/]*}")
    config.add_route("profile_journals_unnamed", "/journals")
    config.add_route("profile_journals", "/journals/{name:[^/]*}")
    config.add_route("profile_collections_unnamed", "/collections")
    config.add_route("profile_collections", "/collections/{name:[^/]*}")
    config.add_route("profile_characters_unnamed", "/characters")
    config.add_route("profile_characters", "/characters/{name:[^/]*}")
    config.add_route("profile_shouts_unnamed", "/shouts")
    config.add_route("profile_shouts", "/shouts/{name:[^/]*}")
    config.add_route("profile_staffnotes_unnamed", "/staffnotes")
    config.add_route("profile_staffnotes", "/staffnotes/{name:[^/]*}")
    config.add_route("profile_favorites_unnamed", "/favorites")
    config.add_route("profile_favorites", "/favorites/{name:[^/]*}")
    config.add_route("profile_friends_unnamed", "/friends")
    config.add_route("profile_friends", "/friends/{name:[^/]*}")
    config.add_route("profile_following_unnamed", "/following")
    config.add_route("profile_following", "/following/{name:[^/]*}")
    config.add_route("profile_followed_unnamed", "/followed")
    config.add_route("profile_followed", "/followed/{name:[^/]*}")
    config.add_route("profile_media", "/~{name}/{link_type}")

    # Submitting, reuploading, and removing content
    config.add_route("reupload_submission", "/reupload/submission")
    config.add_route("reupload_character", "/reupload/character")
    config.add_route("reupload_cover", "/reupload/cover")
    config.add_route("edit_submission", "/edit/submission")
    config.add_route("edit_character", "/edit/character")
    config.add_route("edit_journal", "/edit/journal")
    config.add_route("submit", "/submit")
    config.add_route("submit_visual", "/submit/visual")
    config.add_route("submit_literary", "/submit/literary")
    config.add_route("submit_multimedia", "/submit/multimedia")
    config.add_route("submit_character", "/submit/character")
    config.add_route("submit_journal", "/submit/journal")
    config.add_route("submit_shout", "/submit/shout")
    config.add_route("submit_comment", "/submit/comment")
    config.add_route("submit_report", "/submit/report")
    config.add_route("submit_tags", "/submit/tags")
    config.add_route("remove_submission", "/remove/submission")
    config.add_route("remove_character", "/remove/character")
    config.add_route("remove_journal", "/remove/journal")
    config.add_route("remove_comment", "/remove/comment")

    # Site Updates
    config.add_route("site_update_list", "/site-updates/")
    config.add_route("site_update", "/site-updates/{update_id:[0-9]+}")

    # Two-Factor Authentication views.
    config.add_route("control_2fa_status", "/control/2fa/status")
    config.add_route("control_2fa_init", "/control/2fa/init")
    config.add_route("control_2fa_init_qrcode", "/control/2fa/init_qrcode")
    config.add_route("control_2fa_init_verify", "/control/2fa/init_verify")
    config.add_route("control_2fa_disable", "/control/2fa/disable")
    config.add_route("control_2fa_generate_recovery_codes_verify_password", "/control/2fa/generate_recovery_codes_verify_password")
    config.add_route("control_2fa_generate_recovery_codes", "/control/2fa/generate_recovery_codes")

    config.add_route("policy_community", "/policy/community")
    config.add_route("policy_copyright", "/policy/copyright")
    config.add_route("policy_privacy", "/policy/privacy")
    config.add_route("policy_scoc", "/policy/scoc")
    config.add_route("policy_tos", "/policy/tos")

    config.add_route("staff", "/staff")
    config.add_route("thanks", "/thanks")

    # Help page routes
    config.add_route("help", "/help")
    config.add_route("help_about", "/help/about")
    config.add_route("help_collections", "/help/collections")
    config.add_route("help_faq", "/help/faq")
    config.add_route("help_folders", "/help/folders")
    config.add_route("help_gdocs", "/help/google-drive-embed")
    config.add_route("help_markdown", "/help/markdown")
    config.add_route("help_marketplace", "/help/marketplace")
    config.add_route("help_ratings", "/help/ratings")
    config.add_route("help_reports", "/help/reports")
    config.add_route("help_searching", "/help/searching")
    config.add_route("help_tagging", "/help/tagging")
    config.add_route("help_two_factor_authentication", "/help/two_factor_authentication")
    config.add_route("help_verification", "/help/verification")

    # Management and settings routes.
    config.add_route("control", "/{alias:control|settings}")
    config.add_route("control_alias", "/manage/alias")
    config.add_route("control_apikeys", "/control/apikeys")
    config.add_route("control_avatar", "/manage/avatar")
    config.add_route("control_banner", "/manage/banner")
    config.add_route("control_collection_options", "/control/collections")
    config.add_route("control_collections", "/manage/collections")
    config.add_route("control_createcommishclass", "/control/createcommishclass")
    config.add_route("control_createcommishprice", "/control/createcommishprice")
    config.add_route("control_createfolder", "/control/createfolder")
    config.add_route("control_editcommishclass", "/control/editcommishclass")
    config.add_route("control_editcommishinfo", "/control/editcommishinfo")
    config.add_route("control_editcommishprice", "/control/editcommishprice")
    config.add_route("control_editcommissionsettings", "/control/editcommissionsettings")
    config.add_route("control_editemailpassword", "/control/editemailpassword")
    config.add_route("control_editfolder", "/control/editfolder/{folderid:[0-9]+}")
    config.add_route("control_editpreferences", "/control/editpreferences")
    config.add_route("control_editprofile", "/control/editprofile")
    config.add_route("control_following", "/manage/following")
    config.add_route("control_friends", "/manage/friends")
    config.add_route("control_ignoreuser", "/control/ignoreuser")
    config.add_route("control_manage_follow", "/manage/following/{userid:[0-9]+}")
    config.add_route("control_movefolder", "/control/movefolder")
    config.add_route("control_removecommishclass", "/control/removecommishclass")
    config.add_route("control_removecommishprice", "/control/removecommishprice")
    config.add_route("control_removefolder", "/control/removefolder")
    config.add_route("control_renamefolder", "/control/renamefolder")
    config.add_route("control_sfw_toggle", "/control/sfwtoggle")
    config.add_route("control_streaming", "/control/streaming")
    config.add_route("control_tagfilters", "/manage/tagfilters")
    config.add_route("control_tagrestrictions", "/control/tagrestrictions")
    config.add_route("control_unignoreuser", "/control/unignoreuser")
    config.add_route("control_uploadavatar", "/control/uploadavatar")
    config.add_route("control_username", "/control/username")
    config.add_route("favorite", "/favorite")
    config.add_route("followuser", "/followuser")
    config.add_route("frienduser", "/frienduser")
    config.add_route("ignoreuser", "/ignoreuser")
    config.add_route("manage_folders", "/manage/folders")
    config.add_route("manage_ignore", "/manage/ignore")
    config.add_route("manage_thumbnail_", "/manage/thumbnail")
    config.add_route("unfollowuser", "/unfollowuser")
    config.add_route("unfrienduser", "/unfrienduser")

    # Message routes.
    config.add_route("messages_notifications", "/messages/notifications")
    config.add_route("messages_submissions", "/messages/submissions")
    config.add_route("messages_remove", "/messages/remove")

    # Moderation routes.
    config.add_route("modcontrol", "/modcontrol")
    config.add_route("modcontrol_contentbyuser", "/modcontrol/contentbyuser")
    config.add_route("modcontrol_manageuser", "/modcontrol/manageuser")
    config.add_route("modcontrol_report", "/modcontrol/report")
    config.add_route("modcontrol_reports", "/modcontrol/reports")
    config.add_route("modcontrol_suspenduser", "/modcontrol/suspenduser")
    config.add_route("modcontrol_spamqueue_journal", "/modcontrol/spamqueue/journal")
    config.add_route("modcontrol_spamqueue_submission", "/modcontrol/spamqueue/submission")
    config.add_route("modcontrol_copynotetostaffnotes", "/modcontrol/copynotetostaffnotes")
    config.add_route("modcontrol_closereport", "/modcontrol/closereport")
    config.add_route("modcontrol_massaction", "/modcontrol/massaction")
    config.add_route("modcontrol_hide", "/modcontrol/hide")
    config.add_route("modcontrol_unhide", "/modcontrol/unhide")
    config.add_route("modcontrol_removeavatar", "/modcontrol/removeavatar")
    config.add_route("modcontrol_removebanner", "/modcontrol/removebanner")
    config.add_route("modcontrol_editprofiletext", "/modcontrol/editprofiletext")
    config.add_route("modcontrol_editcatchphrase", "/modcontrol/editcatchphrase")
    config.add_route("modcontrol_spam_remove", "/modcontrol/spam/remove")

    # Admin Control Routes
    config.add_route("admincontrol", "/admincontrol")
    config.add_route("admin_acctverifylink", "/admincontrol/acctverifylink")
    config.add_route("admincontrol_finduser", "/admincontrol/finduser")
    config.add_route("admin_manageuser", "/admincontrol/manageuser")
    config.add_route("admincontrol_pending_accounts", "/admincontrol/pending_accounts")
    config.add_route("admin_siteupdate", "/admincontrol/siteupdate")
    config.add_route("site_update_edit", "/site-updates/{update_id:[0-9]+}/edit")

    # Director control routes.
    config.add_route("directorcontrol", "/directorcontrol")
    config.add_route("directorcontrol_emailblacklist", "/directorcontrol/emailblacklist")
    config.add_route("directorcontrol_globaltagrestrictions", "/directorcontrol/globaltagrestrictions")

    # Notes
    config.add_route("notes_compose", "/notes/compose")
    config.add_route("/notes", "/notes")
    config.add_route("note", "/note")
    config.add_route("notes_remove", "/notes/remove")

    # Collection routes.
    config.add_route("collection_offer", "/collection/offer")
    config.add_route("collection_request", "/collection/request")
    config.add_route("collection_remove", "/collection/remove")
    # OAuth2 routes.
    config.add_route("oauth2_authorize", "/api/oauth2/authorize")
    config.add_route("oauth2_token", "/api/oauth2/token")

    # Routes for static event pages, such as holidays.
    config.add_route("events_halloweasyl2014", "/events/halloweasyl2014")

    # API routes.
    config.add_route("useravatar", "/api/useravatar")
    config.add_route("whoami", "/api/whoami")
    config.add_route("version", r"/api/version{format:(\.[^.]+)?}")
    config.add_route("api_frontpage", "/api/submissions/frontpage")
    config.add_route("api_submission_view", "/api/submissions/{submitid:[0-9]+}/view")
    config.add_route("api_journal_view", "/api/journals/{journalid:[0-9]+}/view")
    config.add_route("api_character_view", "/api/characters/{charid:[0-9]+}/view")
    config.add_route("api_user_view", "/api/users/{login:[^/]+}/view")
    config.add_route("api_user_gallery", "/api/users/{login:[^/]+}/gallery")
    config.add_route("api_messages_submissions", "/api/messages/submissions")
    config.add_route("api_messages_summary", "/api/messages/summary")
    config.add_route("api_favorite", "/api/{content_type:(submissions|characters|journals)}/{content_id:[0-9]+}/favorite")
    config.add_route("api_unfavorite", "/api/{content_type:(submissions|characters|journals)}/{content_id:[0-9]+}/unfavorite")

    config.scan("weasyl.controllers")

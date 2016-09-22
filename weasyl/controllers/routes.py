from __future__ import absolute_import

from collections import namedtuple

from weasyl.controllers import (
    admin,
    ads,
    content,
    detail,
    events,
    general,
    info,
    interaction,
    messages,
    moderation,
    profile,
    settings,
    user,
    weasyl_collections,
)
from weasyl import oauth2


Route = namedtuple('Route', ['pattern', 'name', 'view'])
"""
A route to be added to the Weasyl application.

`view` may be either a view callable (in which case only GET/HEAD requests are routed to it) or a
dict mapping http methods to view callables.
"""


routes = (
    # Front page views.
    Route("/{index:(index)?}", "index", general.index_),  # 'index' is optional in the URL
    Route("/search", "search", general.search_),
    Route("/popular", "popular", general.popular_),
    Route("/streaming", "streaming", general.streaming_),

    # Signin and out views.
    Route("/signin", "signin", {'GET': user.signin_get_, 'POST': user.signin_post_}),
    Route("/signin/unicode-failure", "signin-unicode-failure", {
        'GET': user.signin_unicode_failure_get_, 'POST': user.signin_unicode_failure_post_
    }),
    Route("/signout", "signout", user.signout_),
    Route("/signup", "signup", {'GET': user.signup_get_, 'POST': user.signup_post_}),

    # Verification and password management views.
    Route("/verify/account", "verify_account", user.verify_account_),
    Route("/verify/premium", "verify_premium", user.verify_premium_),
    Route("/forgotpassword", "forgot_password",
          {'GET': user.forgotpassword_get_, 'POST': user.forgetpassword_post_}),
    Route("/resetpassword", "reset_password",
          {'GET': user.resetpassword_get_, 'POST': user.resetpassword_post_}),
    Route("/force/resetpassword", "force_reset_password", {'POST': user.force_resetpassword_}),
    Route("/force/resetbirthday", "force_reset_birthday", {'POST': user.force_resetpassword_}),

    # Profile views.
    Route("/~", "profile_tilde_unnamed", profile.profile_),
    Route("/~{name}", "profile_tilde", profile.profile_),
    Route("/user", "profile_user_unnamed", profile.profile_),
    Route("/user/{name}", "profile_user", profile.profile_),
    Route("/profile", "profile_unnamed", profile.profile_),
    Route("/profile/{name}", "profile", profile.profile_),
    Route("/~{name}/{link_type}", "profile_media", profile.profile_media_),
    Route("/~{name}/{ignore_s:submissions?}/{submitid:[0-9]+}{ignore_name:(/[^/.]*)?}",
          "submission_detail_profile", detail.submission_),
    Route("/~{name}/{linktype}/{submitid:[0-9]+}/{ignore_name:.*}",
          "submission_detail_media", detail.submission_media_),
    Route("/submissions", "profile_submissions_unnamed", profile.submissions_),
    Route("/submissions/{name:[^/]*}", "profile_submissions", profile.submissions_),
    Route("/journals", "profile_journals_unnamed", profile.journals_),
    Route("/journals/{name:[^/]*}", "profile_journals", profile.journals_),
    Route("/collections", "profile_collections_unnamed", profile.collections_),
    Route("/collections/{name:[^/]*}", "profile_collections", profile.collections_),
    Route("/characters", "profile_characters_unnamed", profile.characters_),
    Route("/characters/{name:[^/]*}", "profile_characters", profile.characters_),
    Route("/shouts", "profile_shouts_unnamed", profile.shouts_),
    Route("/shouts/{name:[^/]*}", "profile_shouts", profile.shouts_),
    Route("/favorites", "profile_favorites_unnamed", profile.favorites_),
    Route("/favorites/{name:[^/]*}", "profile_favorites", profile.favorites_),
    Route("/friends", "profile_friends_unnamed", profile.friends_),
    Route("/friends/{name:[^/]*}", "profile_friends", profile.friends_),
    Route("/following", "profile_following_unnamed", profile.following_),
    Route("/following/{name:[^/]*}", "profile_following", profile.following_),
    Route("/followed", "profile_followed_unnamed", profile.followed_),
    Route("/followed/{name:[^/]*}", "profile_followed", profile.followed_),
    Route("/staffnotes", "profile_staffnotes_unnamed", profile.staffnotes_),
    Route("/staffnotes/{name:[^/]*}", "profile_staffnotes", profile.staffnotes_),

    # Details of specific content
    Route("/view", "submission_detail_view_unnamed", detail.submission_),
    Route("/view/{submitid:[0-9]+}{ignore_name:(/.*)?}", "submission_detail_view",
          detail.submission_),
    Route("/submission", "submission_detail_unnamed", detail.submission_),
    Route("/submission/{submitid:[0-9]+}{ignore_name:(/.*)?}", "submission_detail",
          detail.submission_),
    Route("/submission/tag-history/{submitid:[0-9]+}", "submission_tag_history",
          detail.submission_tag_history_),
    Route("/character", "character_detail_unnamed", detail.character_),
    Route("/character/{charid:[0-9]+}*remainder", "character_detail", detail.character_),
    Route("/journal", "journal_detail_unnamedited", detail.journal_),
    Route("/journal/{journalid:[0-9]+}*remainder", "journal_detail", detail.journal_),

    # Submitting, reuploading, and removing content
    Route("/submit", "submit", content.submit_),
    Route("/submit/visual", "submit_visual",
          {'GET': content.submit_visual_get_, 'POST': content.submit_visual_post_}),
    Route("/submit/literary", "submit_literary",
          {'GET': content.submit_literary_get_, 'POST': content.submit_literary_post_}),
    Route("/submit/multimedia", "submit_multimedia",
          {'GET': content.submit_multimedia_get_, 'POST': content.submit_multimedia_post_}),
    Route("/submit/character", "submit_character",
          {'GET': content.submit_character_get_, 'POST': content.submit_character_post_}),
    Route("/submit/journal", "submit_journal",
          {'GET': content.submit_journal_get_, 'POST': content.submit_journal_post_}),
    Route("/submit/shout", "submit_shout", {'POST': content.submit_shout_}),
    Route("/submit/comment", "submit_comment", {'POST': content.submit_comment_}),
    Route("/submit/report", "submit_report", {'POST': content.submit_report_}),
    Route("/submit/tags", "submit_tags", {'POST': content.submit_tags_}),
    Route("/reupload/submission", "reupload_submission",
          {'GET': content.reupload_submission_get_, 'POST': content.reupload_submission_post_}),
    Route("/reupload/character", "reupload_character",
          {'GET': content.reupload_character_get_, 'POST': content.reupload_character_post_}),
    Route("/reupload/cover", "reupload_cover",
          {'GET': content.reupload_cover_get_, 'POST': content.reupload_cover_post_}),
    Route("/edit/submission", "edit_submission",
          {'GET': content.edit_submission_get_, 'POST': content.edit_submission_post_}),
    Route("/edit/character", "edit_character",
          {'GET': content.edit_character_get_, 'POST': content.edit_character_post_}),
    Route("/edit/journal", "edit_journal",
          {'GET': content.edit_journal_get_, 'POST': content.edit_journal_post_}),
    Route("/remove/submission", "remove_submission", {'POST': content.remove_submission_}),
    Route("/remove/character", "remove_character", {'POST': content.remove_character_}),
    Route("/remove/journal", "remove_journal", {'POST': content.remove_journal_}),
    Route("/remove/comment", "remove_comment", {'POST': content.remove_comment_}),

    # Management and settings routes.
    Route("/manage/folders", "manage_folders", settings.manage_folders_),
    Route("/manage/following", "control_following",
          {'GET': settings.manage_following_get_, 'POST': settings.manage_following_post_}),
    Route("/manage/friends", "control_friends", settings.manage_friends_),
    Route("/manage/ignore", "manage_ignore", settings.manage_ignore_),
    Route("/manage/collections", "control_collections",
          {'GET': settings.manage_collections_get_, 'POST': settings.manage_collections_post_}),
    Route("/manage/thumbnail", "manage_thumbnail_",
          {'GET': settings.manage_thumbnail_get_, 'POST': settings.manage_thumbnail_post_}),
    Route("/manage/tagfilters", "control_tagfilters",
          {'GET': settings.manage_tagfilters_get_, 'POST': settings.manage_tagfilters_post_}),
    Route("/manage/avatar", "control_avatar",
          {'GET': settings.manage_avatar_get_, 'POST': settings.manage_avatar_post_}),
    Route("/manage/banner", "control_banner",
          {'GET': settings.manage_banner_get_, 'POST': settings.manage_banner_post_}),
    Route("/manage/alias", "control_alias",
          {'GET': settings.manage_alias_get_, 'POST': settings.manage_alias_post_}),
    Route("/{alias:control|settings}", "control", settings.control_),
    Route("/control/uploadavatar", "control_uploadavatar",
          {'POST': settings.control_uploadavatar_}),
    Route("/control/editprofile", "control_editprofile",
          {'GET': settings.control_editprofile_get_, 'POST': settings.control_editprofile_put_}),
    Route("/control/editcommissionprices", "control_editcommissionprices",
          settings.control_editcommissionprices_),
    Route("/control/editcommishtext", "control_editcommishtext",
          {'POST': settings.control_editcommishtext_}),
    Route("/control/createcommishclass", "control_createcommishclass",
          {'POST': settings.control_createcommishclass_}),
    Route("/control/editcommishclass", "control_editcommishclass",
          {'POST': settings.control_editcommishclass_}),
    Route("/control/removecommishclass", "control_removecommishclass",
          {'POST': settings.control_removecommishclass_}),
    Route("/control/createcommishprice", "control_createcommishprice",
          {'POST': settings.control_createcommishprice_}),
    Route("/control/editcommishprice", "control_editcommishprice",
          {'POST': settings.control_editcommishprice_}),
    Route("/control/removecommishprice", "control_removecommishprice",
          {'POST': settings.control_removecommishprice_}),
    Route("/control/editemailpassword", "control_editemailpassword", {
        'GET': settings.control_editemailpassword_get_,
        'POST': settings.control_editemailpassword_post_
    }),
    Route("/control/editpreferences", "control_editpreferences", {
        'GET': settings.control_editpreferences_get_,
        'POST': settings.control_editpreferences_post_
    }),
    Route("/control/createfolder", "control_createfolder", {'POST': settings.control_createfolder_}),
    Route("/control/renamefolder", "control_renamefolder", {'POST': settings.control_renamefolder_}),
    Route("/control/removefolder", "control_removefolder", {'POST': settings.control_removefolder_}),
    Route("/control/editfolder/{folderid:[0-9]+}", "control_editfolder",
          {'GET': settings.control_editfolder_get_, 'POST': settings.control_editfolder_post_}),
    Route("/control/movefolder", "control_movefolder", {'POST': settings.control_movefolder_}),
    Route("/control/ignoreuser", "control_ignoreuser", {'POST': settings.control_ignoreuser_}),
    Route("/control/unignoreuser", "control_unignoreuser", {'POST': settings.control_unignoreuser_}),
    Route("/control/streaming", "control_streaming",
          {'GET': settings.control_streaming_get_, 'POST': settings.control_streaming_post_}),
    Route("/control/apikeys", "control_apikeys",
          {'GET': settings.control_apikeys_get_, 'POST': settings.control_apikeys_post_}),
    Route("/control/sfwtoggle", "control_sfw_toggle", {'POST': settings.sfw_toggle_}),
    Route("/control/collections", "collection_options",
          {'GET': weasyl_collections.collection_options_get_, 'POST': weasyl_collections.collection_options_post_}),

    Route("/frienduser", "frienduser", {'POST': interaction.frienduser_}),
    Route("/unfrienduser", "unfrienduser", {'POST': interaction.unfrienduser_}),
    Route("/followuser", "followuser", {'POST': interaction.followuser_}),
    Route("/unfollowuser", "unfollowuser", {'POST': interaction.unfollowuser_}),
    Route("/ignoreuser", "ignoreuser", {'POST': interaction.ignoreuser_}),

    Route("/note", "note", interaction.note_),
    Route("/notes", "/notes", interaction.notes_),
    Route("/notes/compose", "notes_compose",
          {'GET': interaction.notes_compose_get_, 'POST': interaction.notes_compose_post_}),
    Route("/notes/remove", "notes_remove", {'POST': interaction.notes_remove_}),

    Route("/favorite", "favorite", {'POST': interaction.favorite_}),

    # Moderation routes.
    Route("/modcontrol", "modcontrol", moderation.modcontrol_),
    Route("/modcontrol/suspenduser", "modcontrol_suspenduser", {
        'GET': moderation.modcontrol_suspenduser_get_,
        'POST': moderation.modcontrol_suspenduser_post_,
    }),
    Route("/modcontrol/report", "modcontrol_report", moderation.modcontrol_report_),
    Route("/modcontrol/reports", "modcontrol_reports", moderation.modcontrol_reports_),
    Route("/modcontrol/closereport", "modcontrol_closereport", {'POST': moderation.modcontrol_closereport_}),
    Route("/modcontrol/contentbyuser", "modcontrol_contentbyuser", moderation.modcontrol_contentbyuser_),
    Route("/modcontrol/massaction", "modcontrol_massaction", {'POST': moderation.modcontrol_massaction_}),
    Route("/modcontrol/hide", "modcontrol_hide", {'POST': moderation.modcontrol_hide_}),
    Route("/modcontrol/unhide", "modcontrol_unhide", {'POST': moderation.modcontrol_unhide_}),
    Route("/modcontrol/manageuser", "modcontrol_manageuser", moderation.modcontrol_manageuser_),
    Route("/modcontrol/removeavatar", "modcontrol_removeavatar", {'POST': moderation.modcontrol_removeavatar_}),
    Route("/modcontrol/removebanner", "modcontrol_removebanner", {'POST': moderation.modcontrol_removebanner_}),
    Route("/modcontrol/editprofiletext", "modcontrol_editprofiletext", {'POST': moderation.modcontrol_editprofiletext_}),
    Route("/modcontrol/editcatchphrase", "modcontrol_editcatchphrase", {'POST': moderation.modcontrol_editcatchphrase_}),
    Route("/modcontrol/edituserconfig", "modcontrol_edituserconfig", {'POST': moderation.modcontrol_edituserconfig_}),

    # Collection routes.
    Route("/collection/offer", "collection_offer", {'POST': weasyl_collections.collection_offer_}),
    Route("/collection/request", "collection_request", {'POST': weasyl_collections.collection_request_}),
    Route("/collection/remove", "collection_remove", {'POST': weasyl_collections.collection_remove_}),

    # Message routes.
    Route("/messages/remove", "messages_remove", {'POST': messages.messages_remove_}),
    Route("/messages/notifications", "messages_notifications", messages.messages_notifications_),
    Route("/messages/submissions", "messages_submissions", messages.messages_submissions_),

    # Admin control routes.
    Route("/admincontrol", "admincontrol", admin.admincontrol_),
    Route("/admincontrol/siteupdate", "admin_siteupdate",
          {'GET': admin.admincontrol_siteupdate_get_, 'POST': admin.admincontrol_siteupdate_post_}),
    Route("/admincontrol/manageuser", "admin_manageuser",
          {'GET': admin.admincontrol_manageuser_get_, 'POST': admin.admincontrol_manageuser_post_}),
    Route("/admincontrol/acctverifylink", "admin_acctverifylink", {'POST': admin.admincontrol_acctverifylink_}),
    Route("/admincontrol/finduser", "admincontrol_finduser", {
        'GET': admin.admincontrol_finduser_get_,
        'POST': admin.admincontrol_finduser_post_,
    }),

    Route("/site-updates/{update_id:[0-9]+}", "site_update", general.site_update_),

    Route("/policy/tos", "policy_tos", info.policy_tos_),
    Route("/policy/privacy", "policy_privacy", info.policy_privacy_),
    Route("/policy/copyright", "policy_copyright", info.policy_copyright_),
    Route("/policy/scoc", "policy_scoc", info.policy_scoc_),
    Route("/policy/community", "policy_community", info.policy_community_),
    Route("/policy/community/changes", "policy_community_changes", info.policy_community_changes_),

    Route("/staff", "staff", info.staff_),
    Route("/thanks", "thanks", info.thanks_),
    Route("/help", "help", info.help_),
    Route("/help/about", "help_about", info.help_about_),
    Route("/help/faq", "help_faq", info.help_faq_),
    Route("/help/collections", "help_collections", info.help_collections_),
    Route("/help/tagging", "help_tagging", info.help_tagging_),
    Route("/help/markdown", "help_markdown", info.help_markdown_),
    Route("/help/searching", "help_searching", info.help_searching_),
    Route("/help/ratings", "help_ratings", info.help_ratings_),
    Route("/help/ratings/changes", "help_ratings_changes", info.help_ratings_changes_),
    Route("/help/folders", "help_folders", info.help_folders_),
    Route("/help/google-drive-embed", "help_gdocs", info.help_gdocs_),
    Route("/help/reports", "help_reports", info.help_reports_),

    # OAuth2 routes.
    Route("/api/oauth2/authorize", "oauth2_authorize",
          {'GET': oauth2.authorize_get_, 'POST': oauth2.authorize_post_}),
    Route("/api/oauth2/token", "oauth2_token", {'POST': oauth2.token_}),

    # Ad routes.
    Route("/ads", "ads", {'GET': ads.list_, 'POST': ads.takedown_}),
    Route("/ads/create", "ads_create", {'GET': ads.create_form_, 'POST': ads.create_}),

    # Routes for static event pages, such as holidays.
    Route("/events/halloweasyl2014", "events_halloweasyl2014", events.halloweasyl2014_),
)


def setup_routes_and_views(config):
    """
    Reponsible for setting up all routes for the Weasyl application.

    Args:
        config: A pyramid Configuration for the wsgi application.
    """
    for route in routes:
        config.add_route(name=route.name, pattern=route.pattern)
        if isinstance(route.view, dict):
            for method in route.view:
                config.add_view(view=route.view[method], route_name=route.name, request_method=method)
        else:
            config.add_view(view=route.view, route_name=route.name, request_method="GET")

    # API routes.
    config.add_route("useravatar", "/api/useravatar")
    config.add_route("whoami", "/api/whoami")
    config.add_route("version", "/api/version{format:(\.[^.]+)?}")
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

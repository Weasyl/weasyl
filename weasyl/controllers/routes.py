from collections import namedtuple

from weasyl.controllers import (
    admin,
    api,
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
    Route("/signin", "signin", {'GET': user.signin_get_, 'POST': user.signin_post_,}),
    Route("/signin/unicode-failure", "signin-unicode-failure", {
        'GET': user.signin_unicode_failure_get_, 'POST': user.signin_unicode_failure_post_,
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
    Route("/journals/{name:[^/]*}", "profile_journals",  profile.journals_),
    Route("/collections", "profile_collections_unnamed",  profile.collections_),
    Route("/collections/{name:[^/]*}", "profile_collections",  profile.collections_),
    Route("/characters", "profile_characters_unnamed",  profile.characters_),
    Route("/characters/{name:[^/]*}", "profile_characters",  profile.characters_),
    Route("/shouts", "profile_shouts_unnamed",  profile.shouts_),
    Route("/shouts/{name:[^/]*}", "profile_shouts",  profile.shouts_),
    Route("/favorites", "profile_favorites_unnamed",  profile.favorites_),
    Route("/favorites/{name:[^/]*}", "profile_favorites",  profile.favorites_),
    Route("/friends", "profile_friends_unnamed",  profile.friends_),
    Route("/friends/{name:[^/]*}", "profile_friends",  profile.friends_),
    Route("/following", "profile_following_unnamed",  profile.following_),
    Route("/following/{name:[^/]*}", "profile_following",  profile.following_),
    Route("/followed", "profile_followed_unnamed",  profile.followed_),
    Route("/followed/{name:[^/]*}", "profile_followed",  profile.followed_),
    Route("/staffnotes", "profile_staffnotes_unnamed",  profile.staffnotes_),
    Route("/staffnotes/{name:[^/]*}", "profile_staffnotes",  profile.staffnotes_),

    Route("/view", "submission_detail_view_unnamed", detail.submission_),
    Route("/view/{submitid:[0-9]+}{ignore_name:(/.*)?}", "submission_detail_view", detail.submission_),
    Route("/submission", "submission_detail_unnamed", detail.submission_),
    Route("/submission/{submitid:[0-9]+}{ignore_name:(/.*)?}", "submission_detail", detail.submission_),
    Route("/submission/tag-history/{submitid:[0-9]+}", "submission_tag_history", detail.submission_tag_history_),
    Route("/character", "character_detail_unnamed", detail.character_),
    Route("/character/{charid:[0-9]+}*remainder", "character_detail", detail.character_),
    Route("/journal", "journal_detail_unnamed", detail.journal_),
    Route("/journal/{journalid:[0-9]+}*remainder", "journal_detail", detail.journal_),

)


controllers = (
    "/submit", "weasyl.controllers.content.submit_",
    "/submit/visual", "weasyl.controllers.content.submit_visual_",
    "/submit/literary", "weasyl.controllers.content.submit_literary_",
    "/submit/multimedia", "weasyl.controllers.content.submit_multimedia_",
    "/submit/character", "weasyl.controllers.content.submit_character_",
    "/submit/journal", "weasyl.controllers.content.submit_journal_",
    "/submit/shout", "weasyl.controllers.content.submit_shout_",
    "/submit/comment", "weasyl.controllers.content.submit_comment_",
    "/submit/report", "weasyl.controllers.content.submit_report_",
    "/submit/tags", "weasyl.controllers.content.submit_tags_",

    "/reupload/submission", "weasyl.controllers.content.reupload_submission_",
    "/reupload/character", "weasyl.controllers.content.reupload_character_",
    "/reupload/cover", "weasyl.controllers.content.reupload_cover_",

    "/edit/submission", "weasyl.controllers.content.edit_submission_",
    "/edit/character", "weasyl.controllers.content.edit_character_",
    "/edit/journal", "weasyl.controllers.content.edit_journal_",

    "/remove/submission", "weasyl.controllers.content.remove_submission_",
    "/remove/character", "weasyl.controllers.content.remove_character_",
    "/remove/journal", "weasyl.controllers.content.remove_journal_",
    "/remove/comment", "weasyl.controllers.content.remove_comment_",

    "/frienduser", "weasyl.controllers.interaction.frienduser_",
    "/unfrienduser", "weasyl.controllers.interaction.unfrienduser_",
    "/followuser", "weasyl.controllers.interaction.followuser_",
    "/unfollowuser", "weasyl.controllers.interaction.unfollowuser_",
    "/ignoreuser", "weasyl.controllers.interaction.ignoreuser_",

    "/note", "weasyl.controllers.interaction.note_",
    "/notes", "weasyl.controllers.interaction.notes_",
    "/notes/compose", "weasyl.controllers.interaction.notes_compose_",
    "/notes/remove", "weasyl.controllers.interaction.notes_remove_",

    "/collection/offer", "weasyl.controllers.collections.collection_offer_",
    "/collection/request", "weasyl.controllers.collections.collection_request_",
    "/collection/remove", "weasyl.controllers.collections.collection_remove_",
    "/collection/acceptoffer", "weasyl.controllers.collections.collection_acceptoffer_",
    "/collection/rejectoffer", "weasyl.controllers.collections.collection_rejectoffer_",

    "/favorite", "weasyl.controllers.interaction.favorite_",

    "/messages/remove", "weasyl.controllers.messages.messages_remove_",
    "/messages/notifications", "weasyl.controllers.messages.messages_notifications_",
    "/messages/submissions", "weasyl.controllers.messages.messages_submissions_",

    "/control", "weasyl.controllers.settings.control_",
    "/settings", "weasyl.controllers.settings.control_",
    "/control/uploadavatar", "weasyl.controllers.settings.control_uploadavatar_",
    "/control/editemailpassword", "weasyl.controllers.settings.control_editemailpassword_",
    "/control/editpreferences", "weasyl.controllers.settings.control_editpreferences_",
    "/control/editprofile", "weasyl.controllers.settings.control_editprofile_",
    "/control/editcommissionprices", "weasyl.controllers.settings.control_editcommissionprices_",
    "/control/editcommishtext", "weasyl.controllers.settings.control_editcommishtext_",
    "/control/createcommishclass", "weasyl.controllers.settings.control_createcommishclass_",
    "/control/editcommishclass", "weasyl.controllers.settings.control_editcommishclass_",
    "/control/removecommishclass", "weasyl.controllers.settings.control_removecommishclass_",
    "/control/createcommishprice", "weasyl.controllers.settings.control_createcommishprice_",
    "/control/editcommishprice", "weasyl.controllers.settings.control_editcommishprice_",
    "/control/removecommishprice", "weasyl.controllers.settings.control_removecommishprice_",
    "/control/createfolder", "weasyl.controllers.settings.control_createfolder_",
    "/control/renamefolder", "weasyl.controllers.settings.control_renamefolder_",
    "/control/removefolder", "weasyl.controllers.settings.control_removefolder_",
    "/control/editfolder/([0-9]+)", "weasyl.controllers.settings.control_editfolder_",
    "/control/movefolder", "weasyl.controllers.settings.control_movefolder_",
    "/control/ignoreuser", "weasyl.controllers.settings.control_ignoreuser_",
    "/control/unignoreuser", "weasyl.controllers.settings.control_unignoreuser_",
    "/control/streaming", "weasyl.controllers.settings.control_streaming_",
    "/control/apikeys", "weasyl.controllers.settings.control_apikeys_",
    "/control/sfwtoggle", "weasyl.controllers.settings.sfwtoggle_",
    "/control/collections", "weasyl.controllers.collections.collection_options_",

    "/manage/folders", "weasyl.controllers.settings.manage_folders_",
    "/manage/following", "weasyl.controllers.settings.manage_following_",
    "/manage/friends", "weasyl.controllers.settings.manage_friends_",
    "/manage/ignore", "weasyl.controllers.settings.manage_ignore_",
    "/manage/collections", "weasyl.controllers.settings.manage_collections_",
    "/manage/thumbnail", "weasyl.controllers.settings.manage_thumbnail_",
    "/manage/tagfilters", "weasyl.controllers.settings.manage_tagfilters_",
    "/manage/avatar", "weasyl.controllers.settings.manage_avatar_",
    "/manage/banner", "weasyl.controllers.settings.manage_banner_",
    "/manage/alias", "weasyl.controllers.settings.manage_alias_",

    "/modcontrol", "weasyl.controllers.moderation.modcontrol_",
    "/modcontrol/finduser", "weasyl.controllers.moderation.modcontrol_finduser_",
    "/modcontrol/suspenduser", "weasyl.controllers.moderation.modcontrol_suspenduser_",
    "/modcontrol/report", "weasyl.controllers.moderation.modcontrol_report_",
    "/modcontrol/reports", "weasyl.controllers.moderation.modcontrol_reports_",
    "/modcontrol/closereport", "weasyl.controllers.moderation.modcontrol_closereport_",
    "/modcontrol/contentbyuser", "weasyl.controllers.moderation.modcontrol_contentbyuser_",
    "/modcontrol/hide", "weasyl.controllers.moderation.modcontrol_hide_",
    "/modcontrol/unhide", "weasyl.controllers.moderation.modcontrol_unhide_",
    "/modcontrol/manageuser", "weasyl.controllers.moderation.modcontrol_manageuser_",
    "/modcontrol/removeavatar", "weasyl.controllers.moderation.modcontrol_removeavatar_",
    "/modcontrol/removebanner", "weasyl.controllers.moderation.modcontrol_removebanner_",
    "/modcontrol/editprofiletext", "weasyl.controllers.moderation.modcontrol_editprofiletext_",
    "/modcontrol/editcatchphrase", "weasyl.controllers.moderation.modcontrol_editcatchphrase_",
    "/modcontrol/edituserconfig", "weasyl.controllers.moderation.modcontrol_edituserconfig_",
    "/modcontrol/massaction", "weasyl.controllers.moderation.modcontrol_massaction_",

    "/admincontrol", "weasyl.controllers.admin.admincontrol_",
    "/admincontrol/siteupdate", "weasyl.controllers.admin.admincontrol_siteupdate_",
    "/admincontrol/manageuser", "weasyl.controllers.admin.admincontrol_manageuser_",
    "/admincontrol/acctverifylink", "weasyl.controllers.admin.admincontrol_acctverifylink_",

    "/site-updates/([0-9]+)", "weasyl.controllers.general.site_update_",

    "/policy/tos", "weasyl.controllers.info.policy_tos_",
    "/policy/privacy", "weasyl.controllers.info.policy_privacy_",
    "/policy/copyright", "weasyl.controllers.info.policy_copyright_",
    "/policy/scoc", "weasyl.controllers.info.policy_scoc_",
    "/policy/community", "weasyl.controllers.info.policy_community_",
    "/policy/community/changes", "weasyl.controllers.info.policy_community_changes_",

    "/staff", "weasyl.controllers.info.staff_",
    "/thanks", "weasyl.controllers.info.thanks_",
    "/help", "weasyl.controllers.info.help_",
    "/help/about", "weasyl.controllers.info.help_about_",
    "/help/faq", "weasyl.controllers.info.help_faq_",
    "/help/collections", "weasyl.controllers.info.help_collections_",
    "/help/tagging", "weasyl.controllers.info.help_tagging_",
    "/help/markdown", "weasyl.controllers.info.help_markdown_",
    "/help/searching", "weasyl.controllers.info.help_searching_",
    "/help/ratings", "weasyl.controllers.info.help_ratings_",
    "/help/ratings/changes", "weasyl.controllers.info.help_ratings_changes_",
    "/help/folders", "weasyl.controllers.info.help_folders_",
    "/help/google-drive-embed", "weasyl.controllers.info.help_gdocs_",
    "/help/reports", "weasyl.controllers.info.help_reports_",

    "/api/useravatar", "weasyl.controllers.api.api_useravatar_",
    "/api/whoami", "weasyl.controllers.api.api_whoami_",
    "/api/version(\.[^.]+)?", "weasyl.controllers.api.api_version_",
    "/api/submissions/frontpage", "weasyl.controllers.api.api_frontpage_",
    "/api/submissions/([0-9]+)/view", "weasyl.controllers.api.api_submission_view_",
    "/api/journals/([0-9]+)/view", "weasyl.controllers.api.api_journal_view_",
    "/api/characters/([0-9]+)/view", "weasyl.controllers.api.api_character_view_",
    "/api/users/([^/]+)/view", "weasyl.controllers.api.api_user_view_",
    "/api/users/([^/]+)/gallery", "weasyl.controllers.api.api_user_gallery_",
    "/api/messages/submissions", "weasyl.controllers.api.api_messages_submissions_",
    "/api/messages/summary", "weasyl.controllers.api.api_messages_summary_",

    "/api/(submissions|characters|journals)/([0-9]+)/favorite", "weasyl.controllers.api.api_favorite_",
    "/api/(submissions|characters|journals)/([0-9]+)/unfavorite", "weasyl.controllers.api.api_unfavorite_",

    "/api/oauth2/authorize", "weasyl.oauth2.authorize_",
    "/api/oauth2/token", "weasyl.oauth2.token_",

    "/events/halloweasyl2014", "weasyl.controllers.events.halloweasyl2014_",
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

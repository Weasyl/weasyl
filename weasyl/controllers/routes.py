from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from typing import Any
from typing import Literal

from pyramid.request import Request

from weasyl.controllers import (
    admin,
    api,
    content,
    detail,
    director,
    general,
    info,
    interaction,
    marketplace,
    messages,
    moderation,
    profile,
    search,
    settings,
    siteupdate,
    two_factor_auth,
    user,
    weasyl_collections,
)
from weasyl.controllers.decorators import csrf_defined


HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
Handler = Callable[[Request], Any]


class Route:
    __slots__ = ("pattern", "name", "handlers", "renderer")

    pattern: str
    name: str
    handlers: Mapping[HttpMethod, Handler]
    renderer: Literal["json"] | None

    def __init__(
        self,
        pattern: str,
        name: str,
        handlers: dict[HttpMethod, Handler] | Handler,
        renderer: Literal["json"] | None = None,
    ):
        self.pattern = pattern
        self.name = name
        self.handlers = handlers if isinstance(handlers, dict) else {"GET": handlers}
        self.renderer = renderer


routes = (
    # Front page views.
    Route("/", "index", general.index_),
    Route("/search", "search", general.search_),
    Route("/api-unstable/search/navigation-counts", "search_navigation_counts", search.navigation_counts),
    Route("/popular", "popular", general.popular_),
    Route("/streaming", "streaming", general.streaming_),
    Route("/marketplace", "marketplace", marketplace.search_),

    # Signin and out views.
    Route("/signin", "signin", {'GET': user.signin_get_, 'POST': user.signin_post_}),
    Route("/signin/2fa-auth", "signin_2fa_auth", {'GET': user.signin_2fa_auth_get_, 'POST': user.signin_2fa_auth_post_}),
    Route("/signout", "signout", {'POST': user.signout_}),
    Route("/signup", "signup", {'GET': user.signup_get_, 'POST': user.signup_post_}),

    # Verification and password management views.
    Route("/verify/account", "verify_account", user.verify_account_),
    Route("/forgotpassword", "forgot_password",
          {'GET': user.forgotpassword_get_, 'POST': user.forgetpassword_post_}),
    Route("/resetpassword", "reset_password",
          {'GET': user.resetpassword_get_, 'POST': user.resetpassword_post_}),
    Route("/verify/emailchange", "verify_emailchange", {'GET': user.verify_emailchange_get_}),
    Route("/vouch", "vouch", {'POST': user.vouch_}),

    # Two-Factor Authentication views.
    Route("/control/2fa/status", "control_2fa_status", {'GET': two_factor_auth.tfa_status_get_}),
    Route("/control/2fa/init", "control_2fa_init",
          {'GET': two_factor_auth.tfa_init_get_, 'POST': two_factor_auth.tfa_init_post_}),
    Route("/control/2fa/init_qrcode", "control_2fa_init_qrcode",
          {'GET': two_factor_auth.tfa_init_qrcode_get_, 'POST': two_factor_auth.tfa_init_qrcode_post_}),
    Route("/control/2fa/init_verify", "control_2fa_init_verify",
          {'GET': two_factor_auth.tfa_init_verify_get_, 'POST': two_factor_auth.tfa_init_verify_post_}),
    Route("/control/2fa/disable", "control_2fa_disable",
          {'GET': two_factor_auth.tfa_disable_get_, 'POST': two_factor_auth.tfa_disable_post_}),
    Route("/control/2fa/generate_recovery_codes_verify_password", "control_2fa_generate_recovery_codes_verify_password",
          {'GET': two_factor_auth.tfa_generate_recovery_codes_verify_password_get_, 'POST': two_factor_auth.tfa_generate_recovery_codes_verify_password_post_}),
    Route("/control/2fa/generate_recovery_codes", "control_2fa_generate_recovery_codes",
          {'GET': two_factor_auth.tfa_generate_recovery_codes_get_, 'POST': two_factor_auth.tfa_generate_recovery_codes_post_}),

    # Profile views.
    Route("/~", "profile_tilde_unnamed", profile.profile_),
    Route("/~{name}", "profile_tilde", profile.profile_),
    Route("/user", "profile_user_unnamed", profile.profile_),
    Route("/user/{name}", "profile_user", profile.profile_),
    Route("/profile", "profile_unnamed", profile.profile_),
    Route("/profile/{name}", "profile", profile.profile_),
    Route("/~{name}/{link_type}", "profile_media", profile.profile_media_),
    Route("/~{name}/submission/{submitid:[0-9]+}",
          "submission_detail_profile;no_s;no_slug", detail.submission_),
    Route("/~{name}/submission/{submitid:[0-9]+}/{slug:[^/.]*}",
          "submission_detail_profile;no_s", detail.submission_),
    Route("/~{name}/submissions/{submitid:[0-9]+}",
          "submission_detail_profile;no_slug", detail.submission_),
    Route("/~{name}/submissions/{submitid:[0-9]+}/{slug:[^/.]*}",
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
    Route(
        "/api-unstable/tag-suggestions/{feature}/{targetid}/{tag}/status",
        "suggested_tag_status",
        {
            "PUT": content.tag_status_put,
            "DELETE": content.tag_status_delete,
        },
    ),
    Route("/api-unstable/tag-suggestions/{feature}/{targetid}/{tag}/feedback", "suggested_tag_feedback",
          {'PUT': content.tag_feedback_put}),
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

    Route("/control/editcommissionsettings", "control_editcommissionsettings",
          settings.control_editcommissionsettings_),
    Route("/control/editcommishinfo", "control_editcommishinfo",
          {'POST': settings.control_editcommishinfo_}),
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

    Route("/control/username", "control_username", {
        'GET': settings.control_username_get_,
        'POST': settings.control_username_post_,
    }),
    Route("/control/editemailpassword", "control_editemailpassword", {
        'GET': settings.control_editemailpassword_get_,
        'POST': settings.control_editemailpassword_post_
    }),
    Route("/control/editpreferences", "control_editpreferences", {
        'GET': settings.control_editpreferences_get_,
        'POST': settings.control_editpreferences_post_
    }),
    Route("/control/tagrestrictions", "control_tagrestrictions", {
        'GET': settings.control_tagrestrictions_get_,
        'POST': settings.control_tagrestrictions_post_
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
    Route("/modcontrol/copynotetostaffnotes", "modcontrol_copynotetostaffnotes", {'POST': moderation.modcontrol_copynotetostaffnotes_post_}),
    Route("/modcontrol/closereport", "modcontrol_closereport", {'POST': moderation.modcontrol_closereport_}),
    Route("/modcontrol/contentbyuser", "modcontrol_contentbyuser", moderation.modcontrol_contentbyuser_),
    Route("/modcontrol/massaction", "modcontrol_massaction", {'POST': moderation.modcontrol_massaction_}),
    Route("/modcontrol/manageuser", "modcontrol_manageuser", moderation.modcontrol_manageuser_),
    Route("/modcontrol/removeavatar", "modcontrol_removeavatar", {'POST': moderation.modcontrol_removeavatar_}),
    Route("/modcontrol/removebanner", "modcontrol_removebanner", {'POST': moderation.modcontrol_removebanner_}),
    Route("/modcontrol/editprofiletext", "modcontrol_editprofiletext", {'POST': moderation.modcontrol_editprofiletext_}),
    Route("/modcontrol/editcatchphrase", "modcontrol_editcatchphrase", {'POST': moderation.modcontrol_editcatchphrase_}),

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
    Route("/admincontrol/manageuser", "admin_manageuser",
          {'GET': admin.admincontrol_manageuser_get_, 'POST': admin.admincontrol_manageuser_post_}),
    Route("/admincontrol/finduser", "admincontrol_finduser", {
        'GET': admin.admincontrol_finduser_get_,
        'POST': admin.admincontrol_finduser_post_,
    }),
    Route("/admincontrol/pending_accounts", "admincontrol_pending_accounts", {
        'GET': admin.admincontrol_pending_accounts_get_,
        'POST': admin.admincontrol_pending_accounts_post_,
    }),

    # Director control routes.
    Route("/directorcontrol", "directorcontrol", director.directorcontrol_),
    Route("/directorcontrol/emailblacklist", "directorcontrol_emailblacklist", {
        'GET': director.directorcontrol_emailblacklist_get_,
        'POST': director.directorcontrol_emailblacklist_post_,
    }),
    Route("/directorcontrol/globaltagrestrictions", "directorcontrol_globaltagrestrictions", {
        'GET': director.directorcontrol_globaltagrestrictions_get_,
        'POST': director.directorcontrol_globaltagrestrictions_post_,
    }),

    Route("/site-updates/", "site_update_list", {
        'GET': siteupdate.site_update_list_,
        'POST': siteupdate.site_update_post_,
    }),
    Route("/site-updates/new", "site_update_new", siteupdate.site_update_new_get_),
    Route("/site-updates/{update_id:[0-9]+}", "site_update", {
        'GET': siteupdate.site_update_get_,
        'POST': siteupdate.site_update_put_,
    }),
    Route("/site-updates/{update_id:[0-9]+}/edit", "site_update_edit", siteupdate.site_update_edit_),

    Route("/policy/community", "policy_community", info.policy_community_),
    Route("/policy/copyright", "policy_copyright", info.policy_copyright_),
    Route("/policy/privacy", "policy_privacy", info.policy_privacy_),
    Route("/policy/scoc", "policy_scoc", info.policy_scoc_),
    Route("/policy/tos", "policy_tos", info.policy_tos_),

    Route("/staff", "staff", info.staff_),
    Route("/thanks", "thanks", info.thanks_),

    # Help page routes
    Route("/help", "help", info.help_),
    Route("/help/about", "help_about", info.help_about_),
    Route("/help/collections", "help_collections", info.help_collections_),
    Route("/help/faq", "help_faq", info.help_faq_),
    Route("/help/folders", "help_folders", info.help_folders_),
    Route("/help/google-drive-embed", "help_gdocs", info.help_gdocs_),
    Route("/help/markdown", "help_markdown", info.help_markdown_),
    Route("/help/marketplace", "help_marketplace", info.help_marketplace_),
    Route("/help/ratings", "help_ratings", info.help_ratings_),
    Route("/help/reports", "help_reports", info.help_reports_),
    Route("/help/searching", "help_searching", info.help_searching_),
    Route("/help/tagging", "help_tagging", info.help_tagging_),
    Route("/help/two_factor_authentication", "help_two_factor_authentication", info.help_two_factor_authentication_),
    Route("/help/verification", "help_verification", info.help_verification_),

    # API routes.
    Route("/api/useravatar", "useravatar", api.api_useravatar_, renderer="json"),
    Route("/api/whoami", "whoami", api.api_whoami_, renderer="json"),
    Route(r"/api/version{format:(\.[^.]+)?}", "version", api.api_version_, renderer="json"),
    Route("/api/submissions/frontpage", "api_frontpage", api.api_frontpage_, renderer="json"),
    Route("/api/submissions/{submitid:[0-9]+}/view", "api_submission_view", api.api_submission_view_, renderer="json"),
    Route("/api/journals/{journalid:[0-9]+}/view", "api_journal_view", api.api_journal_view_, renderer="json"),
    Route("/api/characters/{charid:[0-9]+}/view", "api_character_view", api.api_character_view_, renderer="json"),
    Route("/api/users/{login:[^/]+}/view", "api_user_view", api.api_user_view_, renderer="json"),
    Route("/api/users/{login:[^/]+}/gallery", "api_user_gallery", api.api_user_gallery_, renderer="json"),
    Route("/api/messages/submissions", "api_messages_submissions", api.api_messages_submissions_, renderer="json"),
    Route("/api/messages/summary", "api_messages_summary", api.api_messages_summary_, renderer="json"),
    Route("/api/{content_type:(submissions|characters|journals)}/{content_id:[0-9]+}/favorite", "api_favorite", {'POST': api.api_favorite_}, renderer="json"),
    Route("/api/{content_type:(submissions|characters|journals)}/{content_id:[0-9]+}/unfavorite", "api_unfavorite", {'POST': api.api_unfavorite_}, renderer="json"),
    Route("/api-unstable/{content_type:(submissions|characters|journals|users)}/{content_id:[0-9]+}/views/", "view", {'POST': content.views_post}),
)


def setup_routes_and_views(config):
    """
    Reponsible for setting up all routes for the Weasyl application.

    Args:
        config: A pyramid Configuration for the wsgi application.
    """
    for route in routes:
        config.add_route(name=route.name, pattern=route.pattern)
        for method, handler in route.handlers.items():
            if method != "GET" and (handler.__module__, handler.__qualname__) not in csrf_defined:
                raise RuntimeError(f"{handler} has no explicit CSRF policy")

            config.add_view(
                view=handler,
                route_name=route.name,
                request_method=method,
                renderer=route.renderer,
            )

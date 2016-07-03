from libweasyl import staff

from weasyl import define, profile, report
from weasyl.controllers.decorators import controller_base


# Policy functions
class staff_(controller_base):
    def GET(self):
        directors = staff.DIRECTORS
        technical = staff.TECHNICAL - staff.DIRECTORS
        admins = staff.ADMINS - staff.DIRECTORS - staff.TECHNICAL
        mods = staff.MODS - staff.ADMINS
        devs = staff.DEVELOPERS
        staff_info_map = profile.select_avatars(list(directors | technical | admins | mods | devs))
        staff_list = []
        for name, userids in [('Directors', directors),
                              ('Administrators', admins),
                              ('Moderators', mods),
                              ('Techs', technical),
                              ('Developers', devs)]:
            users = [staff_info_map[u] for u in userids]
            users.sort(key=lambda info: info['username'].lower())
            staff_list.append((name, users))

        return define.webpage(self.user_id, "help/staff.html", [staff_list],
                              title="Staff")


class policy_tos_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/tos.html",
                              title="Terms of Service")


class thanks_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/thanks.html",
                              title="Awesome People")


class policy_privacy_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/privacy.html",
                              title="Privacy Policy")


class policy_copyright_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/copyright.html",
                              title="Copyright Policy")


class policy_scoc_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/scoc.html",
                              title="Staff Code of Conduct")


class policy_community_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/community.html",
                              title="Community Guidelines")


class policy_community_changes_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/community-changes.html",
                              title="Community Guidelines")


# Help functions
class help_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/help.html",
                              title="Help Topics")


class help_about_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/about.html",
                              title="About Weasyl")


class help_faq_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/faq.html",
                              title="FAQ")


class help_collections_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/collections.html",
                              title="Collections")


class help_tagging_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/tagging.html",
                              title="Tagging")


class help_searching_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/searching.html",
                              title="Searching")


class help_markdown_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/markdown.html",
                              title="Markdown")


class help_ratings_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/ratings.html",
                              title="Content Ratings")


class help_ratings_changes_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/ratings-changes.html",
                              title="Content Ratings")


class help_gdocs_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/gdocs.html",
                              title="Google Drive Embedding")


class help_folders_(controller_base):
    def GET(self):
        return define.webpage(self.user_id, "help/folder-options.html",
                              title="Folder Options")


class help_reports_(controller_base):
    login_required = True

    def GET(self):
        return define.webpage(self.user_id, "help/reports.html", [
            report.select_reported_list(self.user_id),
        ])

from __future__ import absolute_import

import os

from libweasyl import ratings


MACRO_EMAIL_ADDRESS = "weasyl@weasyl.com"
MACRO_SUPPORT_ADDRESS = "support@weasyl.dev"

MACRO_BCRYPT_ROUNDS = 13

# Example input (userid, "su")
MACRO_IGNOREUSER = " AND NOT EXISTS (SELECT 0 FROM ignoreuser WHERE (userid, otherid) = (%i, %s.userid))"

# Example input (userid, userid)
MACRO_BLOCKTAG_SUBMIT = (
    " AND (su.userid = %i OR NOT EXISTS (SELECT 0 FROM searchmapsubmit"
    " WHERE targetid = su.submitid"
    " AND tagid IN (SELECT tagid FROM blocktag WHERE userid = %i AND rating <= su.rating)))")

# Example input (userid, userid)
MACRO_BLOCKTAG_CHAR = (
    " AND (ch.userid = %i OR NOT EXISTS (SELECT 0 FROM searchmapchar"
    " WHERE targetid = ch.charid AND tagid IN (SELECT tagid FROM blocktag WHERE userid = %i AND rating <= ch.rating)))")

# Example input (userid, userid)
MACRO_BLOCKTAG_JOURNAL = (
    " AND (jo.userid = %i OR NOT EXISTS (SELECT 0 FROM searchmapjournal"
    " WHERE targetid = jo.journalid AND tagid IN (SELECT tagid FROM blocktag"
    " WHERE userid = %i AND rating <= jo.rating)))")

# Example input (userid, userid, userid)
MACRO_FRIENDUSER_SUBMIT = (
    " AND (su.settings !~ 'f' OR su.userid = %i OR EXISTS (SELECT 0 FROM frienduser"
    " WHERE ((userid, otherid) = (%i, su.userid) OR (userid, otherid) = (su.userid, %i)) AND settings !~ 'p'))")

# Example input (userid, userid, userid)
MACRO_FRIENDUSER_JOURNAL = (
    " AND (jo.settings !~ 'f' OR jo.userid = %i OR EXISTS (SELECT 0 FROM frienduser"
    " WHERE ((userid, otherid) = (%i, jo.userid) OR (userid, otherid) = (jo.userid, %i)) AND settings !~ 'p'))")

# Example input (userid, userid, userid)
MACRO_FRIENDUSER_CHARACTER = (
    " AND (ch.settings !~ 'f' or ch.userid = %i OR EXISTS (SELECT 0 from frienduser"
    " WHERE ((userid, otherid) = (%i, ch.userid) OR (userid, otherid) = (ch.userid, %i)) AND settings !~ 'p'))")

MACRO_SUBCAT_LIST = [
    [1010, "Sketch"],
    [1020, "Traditional"],
    [1030, "Digital"],
    [1040, "Animation"],
    [1050, "Photography"],
    [1060, "Design / Interface"],
    [1070, "Modeling / Sculpture"],
    [1075, "Crafts / Jewelry"],
    [1078, "Sewing / Knitting"],
    [1080, "Desktop / Wallpaper"],
    [1999, "Other"],
    [2010, "Story"],
    [2020, "Poetry / Lyrics"],
    [2030, "Script / Screenplay"],
    [2999, "Other"],
    [3010, "Original Music"],
    [3020, "Cover Version"],
    [3030, "Remix / Mashup"],
    [3040, "Speech / Reading"],
    [3500, "Embedded Video"],
    [3999, "Other"],
]


# Mod actions which apply to all submissions
MACRO_MOD_ACTIONS = [
    # Line below is so default mod action is 'nothing'. Intentional behavior.
    ('null', ''),
    ('hide', 'Hide'),
    ('show', 'Show'),
] + [('rate-%s' % (r.code,), 'Rate %s' % (r.name,)) for r in ratings.ALL_RATINGS] + [
    ('clearcritique', 'Remove critique-requested flag'),
    ('setcritique', 'Set critique-requested flag'),
]


def MACRO_MOD_ACTIONS_FOR_SETTINGS(settings, submission_type):
    # We start with the complete list of mod actions, then filter it based on submission_type
    valid_list = MACRO_MOD_ACTIONS

    # Journals and characters can't have the critique flag set
    if submission_type in ("journal", "character"):
        valid_list = [(a, b) for a, b in valid_list if not a.endswith('critique')]

    # Select whether we show 'Show' or 'Hide' depending on whether the
    # submission is hidden
    if 'h' in settings:
        valid_list = [(a, b) for a, b in valid_list if a != 'hide']
    else:
        valid_list = [(a, b) for a, b in valid_list if a != 'show']

    # Select whether we show 'Set Critique' or 'Clear Critique' depending on
    # whether the Critique Requested flag is set
    if 'q' in settings:
        valid_list = [(a, b) for a, b in valid_list if a != 'setcritique']
    else:
        valid_list = [(a, b) for a, b in valid_list if a != 'clearcritique']

    # Return our shiny, filtered list of mod actions
    return valid_list


MACRO_REPORT_URGENCY = [
    (10, "Urgent"),
    (20, "Normal"),
    (30, "Trivial"),
]

MACRO_REPORT_VIOLATION = [
    # fields: id, urgency, text, comment_required
    # id must be unique
    # urgency is no longer used, but refers to MACRO_REPORT_URGENCY
    # text is the text which describes this type of violation
    # comment_required: whether the user must submit a comment with this report type

    # Mod comments
    (0, 0, "Comment", False),

    # Report user
    (1010, 10, "Inappropriate avatar", False),
    (1020, 10, "Inappropriate profile picture", False),
    (1030, 20, "Spam or alternate account", False),
    (1999, 20, "Other (please comment)", True),

    # Report submission or character
    (2010, 20, "Harassing content", False),
    (2020, 30, "Tracing or plagiarism", True),
    (2030, 10, "Rapidly flashing colors", False),
    (2040, 10, "Incorrect content rating", False),
    (2050, 20, "Perpetual incorrect tagging", False),
    (2060, 30, "Low-quality photography", False),
    (2065, 30, "Low-quality literature", False),
    (2070, 20, "Spamming or flooding", False),
    (2080, 20, "Meme or image macro", False),
    (2090, 20, "Unacceptable screenshot", False),
    (2110, 10, "Illegal content", False),
    (2120, 10, "Photographic pornography", False),
    (2130, 10, "Offensive content", False),
    (2140, 10, "Misleading thumbnail", False),
    (2999, 20, "Other (please comment)", True),

    # Report journal
    (3010, 20, "Harassing content", False),
    (3020, 20, "Spamming or flooding", False),
    (3030, 10, "Illegal activity", False),
    (3040, 10, "Offensive content", False),
    (3999, 20, "Other (please comment)", True),

    # Report shout or comment
    (4010, 20, "Harassing comment", False),
    (4020, 20, "Spamming or flooding", False),
    (4030, 20, "Inappropriate comment", False),
    (4999, 20, "Other (please comment)", True),
]

MACRO_APP_ROOT = os.environ['WEASYL_APP_ROOT'] + "/"
MACRO_STORAGE_ROOT = os.environ['WEASYL_STORAGE_ROOT'] + "/"

MACRO_URL_CHAR_PATH = "static/character/"

MACRO_SYS_CHAR_PATH = os.path.join(MACRO_STORAGE_ROOT, MACRO_URL_CHAR_PATH)

MACRO_SYS_LOG_PATH = os.path.join(MACRO_STORAGE_ROOT, "log/")
MACRO_SYS_TEMP_PATH = os.path.join(MACRO_STORAGE_ROOT, "temp/")
MACRO_SYS_CONFIG_PATH = os.path.join(MACRO_APP_ROOT, "config/")
MACRO_SYS_STAFF_CONFIG_PATH = os.path.join(MACRO_SYS_CONFIG_PATH, "weasyl-staff.py")

MACRO_CFG_SITE_CONFIG = MACRO_SYS_CONFIG_PATH + "site.config.txt"

SOCIAL_SITES = {
    "deviantart": {
        "name": "DeviantArt",
        "url": "https://www.deviantart.com/%s",
    },
    "facebook": {
        "name": "Facebook",
        "url": "https://www.facebook.com/%s",
    },
    "flickr": {
        "name": "Flickr",
        "url": "https://www.flickr.com/photos/%s",
    },
    "furaffinity": {
        "name": "Fur Affinity",
        "url": "https://www.furaffinity.net/user/%s",
    },
    "googleplus": {
        "name": "Google+",
        "url": "https://plus.google.com/+%s",
    },
    "inkbunny": {
        "name": "Inkbunny",
        "url": "https://inkbunny.net/%s",
    },
    "reddit": {
        "name": "reddit",
        "url": "https://www.reddit.com/user/%s",
    },
    "sofurry": {
        "name": "SoFurry",
        "url": "https://%s.sofurry.com/",
    },
    "steam": {
        "name": "Steam",
        "url": "https://steamcommunity.com/id/%s",
    },
    "tumblr": {
        "name": "Tumblr",
        "url": "https://%s.tumblr.com/",
    },
    "twitter": {
        "name": "Twitter",
        "url": "https://twitter.com/%s",
    },
    "youtube": {
        "name": "YouTube",
        "url": "https://www.youtube.com/user/%s",
    },
    "patreon": {
        "name": "Patreon",
        "url": "https://www.patreon.com/%s",
    },
}

SOCIAL_SITES_BY_NAME = {v['name']: v for v in SOCIAL_SITES.itervalues()}


ART_SUBMISSION_CATEGORY = 1000
TEXT_SUBMISSION_CATEGORY = 2000
MULTIMEDIA_SUBMISSION_CATEGORY = 3000
ALL_SUBMISSION_CATEGORIES = [
    ART_SUBMISSION_CATEGORY,
    TEXT_SUBMISSION_CATEGORY,
    MULTIMEDIA_SUBMISSION_CATEGORY,
]


CONTYPE_PARSABLE_MAP = {
    10: 'submission',
    20: 'character',
    30: 'journal',
    40: 'usercollect',
}

CATEGORY_PARSABLE_MAP = {
    ART_SUBMISSION_CATEGORY: 'visual',
    TEXT_SUBMISSION_CATEGORY: 'literary',
    MULTIMEDIA_SUBMISSION_CATEGORY: 'multimedia',
}

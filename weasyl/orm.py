from __future__ import absolute_import

from libweasyl.models.api import OAuthBearerToken, OAuthConsumer, APIToken
from libweasyl.models.content import Character, Comment, Journal, Submission
from libweasyl.models.media import (
    MediaItem, SubmissionMediaLink, UserMediaLink, MediaMediaLink)
from libweasyl.models.users import Follow, Login, Profile, Session, UserTimezone


# TODO: Implement these are real models in libweasyl.
# These currently exist for a workaround in the settings controller and should be removed.
class CommishClass(object):
    pass


class CommishPrice(object):
    pass


__all__ = [
    'Character', 'Comment', 'Journal', 'Submission',
    'MediaItem', 'SubmissionMediaLink', 'UserMediaLink', 'MediaMediaLink',
    'OAuthBearerToken', 'OAuthConsumer', 'APIToken',
    'Follow', 'Login', 'Profile', 'Session', 'UserTimezone',
    'CommishClass', 'CommishPrice',
]
